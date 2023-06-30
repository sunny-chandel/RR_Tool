from flask import Flask, render_template, request, send_file
import pandas as pd
from T_Discover import process_data
import tempfile
from io import StringIO

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')


@app.route('/index')
def index():
    return render_template('index.html')    

@app.route('/rdl', methods=['POST'])
def process_rdl_files():
    # Create a temporary folder to store the uploaded files
    temp_folder = tempfile.mkdtemp()

    # Save the uploaded files to the temporary folder
    files = request.files.getlist('files[]')
    for file in files:
        file.save(os.path.join(temp_folder, file.filename))

    # Pass the temporary folder path to the RDL script
    rdl_script(temp_folder)

    return 'RDL files processed successfully!'


@app.route('/process', methods=["GET", "POST"])
def process():
    if request.method == 'POST':
        # Read the uploaded CSV file as a string buffer
        csv_file = request.files['csv_file']
        csv_content = csv_file.read().decode('utf-8')
        csv_buffer = StringIO(csv_content.strip())
        
        # Read the string buffer as a DataFrame
        df = pd.read_csv(csv_buffer)
        
        # Save the DataFrame to a temporary location
        temp_path = tempfile.mktemp(suffix='.csv')
        df.to_csv(temp_path, index=False)
        
        # Get the range values from the form
        range1_low = float(request.form['range1_low'])
        range1_high = float(request.form['range1_high'])
        range2_low = float(request.form['range2_low'])
        range2_high = float(request.form['range2_high'])
        range3_low = float(request.form['range3_low'])
        range3_high = float(request.form['range3_high'])
        range4_low = float(request.form['range4_low'])
        range4_high = float(request.form['range4_high'])
        
        # Process the data and get the output DataFrames
        df_score_0_29, df_score_30_69, df_score_threshold_1, df_score_threshold_2, reports_not_in_top2_buckets,unique_count = process_data(df, range1_low, range1_high, range2_low, range2_high, range3_low, range3_high, range4_low, range4_high)
        
        df_score_threshold_1_groups = int(df_score_0_29["Group"].nunique())
        print(df_score_threshold_1_groups)
        df_score_threshold_2_groups = int(df_score_30_69["Group"].nunique())
        print(df_score_threshold_2_groups)
        df_score_threshold_3_groups = int(df_score_threshold_1["Group"].nunique())
        print(df_score_threshold_3_groups)
        df_score_threshold_4_groups = int(df_score_threshold_2["Group"].nunique())
        print(df_score_threshold_4_groups)
        print(unique_count)
        df_score_threshold_3_unquie_report_count = int(df_score_threshold_1["Report"].nunique())
        print(df_score_threshold_3_unquie_report_count)
        df_score_threshold_4_unquie_report_count = int(df_score_threshold_2["Report"].nunique())
       


        # Generate the Excel file with output DataFrames
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        with pd.ExcelWriter(temp_file.name) as writer:
            df_score_0_29.to_excel(writer, sheet_name=f"DataFrame {range1_low}-{range1_high}", index=False)
            df_score_30_69.to_excel(writer, sheet_name=f"DataFrame {range2_low}-{range2_high}", index=False)
            df_score_threshold_1.to_excel(writer, sheet_name=f"DataFrame {range3_low}-{range3_high}", index=False)
            df_score_threshold_2.to_excel(writer, sheet_name=f"DataFrame {range4_low}-{range4_high}", index=False)
            reports_not_in_top2_buckets.to_excel(writer, sheet_name='reports_not_in_top2_buckets', index=False)
        
        # Render the result template and pass the necessary data
        input_table = df_score_0_29.to_html()
        temp_file_path = temp_file.name
        return render_template('result.html', input_table=input_table,
                               temp_path=temp_path,
                               temp_file_path=temp_file_path,
                               df_score_0_29=df_score_0_29,
                               df_score_30_69=df_score_30_69,
                               df_score_threshold_1=df_score_threshold_1,
                               df_score_threshold_2=df_score_threshold_2,
                               reports_not_in_top2_buckets=reports_not_in_top2_buckets,
                               df_score_threshold_1_groups=df_score_threshold_1_groups,
                               df_score_threshold_2_groups=df_score_threshold_2_groups,
                               df_score_threshold_3_groups=df_score_threshold_3_groups,
                               df_score_threshold_4_groups=df_score_threshold_4_groups,
                               unique_count=unique_count,
                               df_score_threshold_3_unquie_report_count=df_score_threshold_3_unquie_report_count,
                               df_score_threshold_4_unquie_report_count=df_score_threshold_4_unquie_report_count )
    else:
        # Code for handling GET request
        return render_template('index.html')

@app.route('/download', methods=["GET"])
def download():
    temp_file_path = request.args.get('temp_file_path')
    return send_file(temp_file_path, as_attachment=True, download_name='output_data.xlsx')

@app.route('/summary')
def summary():
    # Retrieve the necessary variables from the request arguments
    df_score_threshold_1_groups = int(request.args.get('df_score_threshold_1_groups'))
    df_score_threshold_2_groups = int(request.args.get('df_score_threshold_2_groups'))
    df_score_threshold_3_groups = int(request.args.get('df_score_threshold_3_groups'))
    df_score_threshold_4_groups = int(request.args.get('df_score_threshold_4_groups'))
    unique_count = int(request.args.get('unique_count'))
    df_score_threshold_3_unquie_report_count = int(request.args.get('df_score_threshold_3_unquie_report_count'))
    df_score_threshold_4_unquie_report_count = int(request.args.get('df_score_threshold_4_unquie_report_count'))
    
    unique_reports_in_range3_and_4 = df_score_threshold_3_unquie_report_count + df_score_threshold_4_unquie_report_count
    unique_groups_in_range3_and_4 = df_score_threshold_3_groups + df_score_threshold_4_groups
    remaining_reports = unique_count - (df_score_threshold_3_unquie_report_count + df_score_threshold_4_unquie_report_count)

    # Render the summary template and pass the variables to it
    return render_template('summary.html', df_score_threshold_1_groups=df_score_threshold_1_groups,
                           df_score_threshold_2_groups=df_score_threshold_2_groups,
                           df_score_threshold_3_groups=df_score_threshold_3_groups,
                           df_score_threshold_4_groups=df_score_threshold_4_groups,
                           unique_count=unique_count,
                           unique_reports_in_range3_and_4=unique_reports_in_range3_and_4,
                           unique_groups_in_range3_and_4=unique_groups_in_range3_and_4,
                           remaining_reports=remaining_reports)

@app.route('/help')
def help():
    return render_template('help.html')

if __name__ == '__main__':
    app.run()

