import argparse
import json
import logging
import os
import time
import sys
import numpy as np
import pandas as pd
import yaml
def write_error_json(filepath, version, message):
    error_payload={"version": version if version else "unknown","status": "error","error_message": message}
    with open(filepath,'w') as f:
        json.dump(error_payload, f,indent=2)
    print(json.dumps(error_payload,indent=2))
def main():
    parser=argparse.ArgumentParser(description="Primetrade MLOps Batch Signal Pipeline.")
    parser.add_argument("--input",required=True,help="Path to input data.csv")
    parser.add_argument("--config",required=True,help="Path to config.yaml")
    parser.add_argument("--output",required=True,help="Path to save metrics.json")
    parser.add_argument("--log-file",required=True,help="Path to save run.log")
    try:
        args=parser.parse_args()
    except SystemExit:
        write_error_json("metrics.json","unknown","Invalid CLI execution arguments provided.")
        sys.exit(1)
    logging.basicConfig(filename=args.log_file,filemode='w',level=logging.INFO,format='%(asctime)s [%(levelname)s] %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logger=logging.getLogger("MLOpsPipeline")
    logger.info("Batch Pipeline Job initialization sequence started.")
    start_time=time.time()
    config_version="unknown"
    try:
        logger.info(f"Loading runtime target configuration from: {args.config}")
        if not os.path.exists(args.config):
            raise FileNotFoundError(f"Configuration target file not found at: {args.config}")
        with open(args.config, 'r') as f:
            try:
                config=yaml.safe_load(f)
            except yaml.YAMLError as ye:
                raise ValueError(f"Invalid YAML structural format: {str(ye)}")
        if not config or not all(k in config for k in ('seed','window','version')):
            raise KeyError("Configuration missing mandatory parameter mapping fields: seed, window, or version.")
        seed=config['seed']
        window=config['window']
        config_version=config['version']
        np.random.seed(seed)
        logger.info(f"Configuration successfully validated. Version: {config_version}, Window: {window}, Seed: {seed}")
        logger.info(f"Reading ingestion source dataset path from: {args.input}")
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Source data execution file not found at target: {args.input}")
        if os.path.getsize(args.input)==0:
            raise ValueError("Target dataset ingestion path file is completely empty.")
        try:
            with open(args.input,"r",encoding="utf-8-sig") as f:
                lines=[line.strip().replace('"','').replace("'",'') for line in f.readlines() if line.strip()]
            headers=[col.strip().lower() for col in lines[0].split(",")]
            data_rows=[row.split(",") for row in lines[1:]]
            df=pd.DataFrame(data_rows,columns=headers)
            if "close" not in df.columns:
                close_matches=[c for c in df.columns if "close" in c]
                if close_matches:
                    df=df.rename(columns={close_matches[0]:"close"})
                elif len(df.columns)>=5:
                    df=df.rename(columns={df.columns[4]:"close"})
                else:
                    df=df.rename(columns={df.columns[-1]:"close"})
        except Exception as ce:
            raise ValueError(f"Invalid CSV layout or parsing schema error: {str(ce)}")
        df["close"]=pd.to_numeric(df["close"].astype(str).str.strip(),errors="coerce")
        df=df.dropna(subset=["close"])
        rows_loaded=len(df)
        logger.info(f"Dataset successfully ingested into workspace dataframe. Total rows: {rows_loaded}")
        if rows_loaded==0:
            raise ValueError("Ingested dataset contains zero transactional records or data frames.")
        logger.info(f"Calculating rolling mean vectors using window step parameter size: {window}")
        df["rolling_mean"]=df["close"].rolling(window=window).mean()
        df["signal"]=np.where(df["rolling_mean"].isna(),np.nan,np.where(df["close"]>df["rolling_mean"],1.0,0.0))
        logger.info("Signal array evaluation matrix generation complete.")
        valid_signals=df['signal'].dropna()
        if len(valid_signals)==0:
            signal_rate=0.0
        else:
            signal_rate=float(valid_signals.mean())
        latency_ms=int((time.time()-start_time)*1000)
        success_payload={"version":config_version,"rows_processed":rows_loaded,"metric":"signal_rate","value":round(signal_rate,4),
                         "latency_ms":max(1,latency_ms),"seed":seed,"status":"success"}
        with open(args.output,'w') as f:
            json.dump(success_payload,f,indent=2)
        print(json.dumps(success_payload,indent=2))
        logger.info(f"Pipeline job completed successfully. Signal Rate: {success_payload['value']},Latency: {success_payload['latency_ms']}ms")
        sys.exit(0)
    except Exception as e:
        error_msg=str(e)
        logger.error(f"Pipeline failure encountered during runtime: {error_msg}")
        write_error_json(args.output,config_version,error_msg)
        sys.exit(1)
if __name__ == "__main__":
    main()