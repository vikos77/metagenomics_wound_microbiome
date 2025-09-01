#!/bin/bash
# Create download script for better error handling

mkdir -p raw_data
cd raw_data

# Create log files
touch download_success.log
touch download_errors.log

while read run_id; do
    echo "$(date): Starting download of $run_id" | tee -a download_success.log
    
    if fasterq-dump "$run_id" --progress --threads 4; then
        echo "$(date): SUCCESS - $run_id downloaded" | tee -a download_success.log
    else
        echo "$(date): ERROR - Failed to download $run_id" | tee -a download_errors.log
        # Continue with next sample rather than stopping
    fi
    
    # Add small delay to avoid overwhelming the server
    sleep 2
done < ../all_run_ids.txt

echo "Download complete! Check logs for any errors."
