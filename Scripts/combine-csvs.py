import os
import pandas as pd
import csv

def combine_csv_files(input_folder, output_file):
    """
    Combine multiple CSV files with the same columns into one CSV file while maintaining the original delimiter and format.
    
    :param input_folder: Folder containing CSV files to merge.
    :param output_file: Path to the output CSV file.
    """
    all_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    
    if not all_files:
        print("No CSV files found in the directory.")
        return
    
    df_list = [pd.read_csv(os.path.join(input_folder, file), delimiter=';', dtype=str, header=None, quoting=csv.QUOTE_ALL) for file in all_files]
    combined_df = pd.concat(df_list, ignore_index=True)
    
    combined_df.to_csv(output_file, index=False, sep=';', header=False, quoting=csv.QUOTE_ALL)
    print(f"Combined {len(all_files)} CSV files into {output_file}")

if __name__ == "__main__":
    input_folder = "C:/SAL-9543-Batch/out-particulars/to-combine"  # Change this to your folder path
    output_file = "C:/SAL-9543-Batch/out-particulars/out-position-combined.csv"  # Change this to your desired output file name
    combine_csv_files(input_folder, output_file)