
from fpdf import FPDF
import math

import stark_core

name = "STARK Utilities"

def compose_report_operators_and_parameters(key, data):
    composed_filter_dict = {"filter_string":"","expression_values": {}}
    if data['operator'] == "IN":
        string_split = data['value'].split(',')
        composed_filter_dict['filter_string'] += f" {key} IN "
        temp_in_string = ""
        in_string = ""
        in_counter = 1
        composed_filter_dict['report_params'] = {key : f"Is in {data['value']}"}
        for in_index in string_split:
            in_string += f" :inParam{in_counter}, "
            composed_filter_dict['expression_values'][f":inParam{in_counter}"] = {data['type'] : in_index.strip()}
            in_counter += 1
        temp_in_string = in_string[1:-2]
        composed_filter_dict['filter_string'] += f"({temp_in_string}) AND"
    elif data['operator'] in [ "contains", "begins_with" ]:
        composed_filter_dict['filter_string'] += f" {data['operator']}({key}, :{key}) AND"
        composed_filter_dict['expression_values'][f":{key}"] = {data['type'] : data['value'].strip()}
        composed_filter_dict['report_params'] = {key : f"{data['operator'].capitalize().replace('_', ' ')} {data['value']}"}
    elif data['operator'] == "between":
        from_to_split = data['value'].split(',')
        composed_filter_dict['filter_string'] += f" ({key} BETWEEN :from{key} AND :to{key}) AND"
        composed_filter_dict['expression_values'][f":from{key}"] = {data['type'] : from_to_split[0].strip()}
        composed_filter_dict['expression_values'][f":to{key}"] = {data['type'] : from_to_split[1].strip()}
        composed_filter_dict['report_params'] = {key : f"Between {from_to_split[0].strip()} and {from_to_split[1].strip()}"}
    else:
        composed_filter_dict['filter_string'] += f" {key} {data['operator']} :{key} AND"
        composed_filter_dict['expression_values'][f":{key}"] = {data['type'] : data['value'].strip()}
        operator_string_equivalent = ""
        if data['operator'] == '=':
            operator_string_equivalent = 'Is equal to'
        elif data['operator'] == '>':
            operator_string_equivalent = 'Is greater than'
        elif data['operator'] == '>=':
            operator_string_equivalent = 'Is greater than or equal to'
        elif data['operator'] == '<':
            operator_string_equivalent = 'Is less than'
        elif data['operator'] == '<=':
            operator_string_equivalent = 'Is greater than or equal to'
        elif data['operator'] == '<=':
            operator_string_equivalent = 'Is not equal to'
        else:
            operator_string_equivalent = 'Invalid operator'
        composed_filter_dict['report_params'] = {key : f" {operator_string_equivalent} {data['value'].strip()}" }

    return composed_filter_dict

def create_pdf(header_tuple, data_tuple, report_params, pk_field, metadata):

    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    with_total_row = False
    line_height = pdf.font_size * 2.5
    row_number_width = 10
    col_width = pdf.epw / len(header_tuple)  # distribute content evenly
    col_width = col_width + (col_width - row_number_width) / (len(header_tuple) -1)

    render_page_header(pdf, line_height, report_params, pk_field)
    render_table_header(pdf, header_tuple, col_width, line_height, row_number_width) 
    
    for index in header_tuple:
        if index != "#":
            if metadata[index.replace(" ","_")]["data_type"] == 'number':
                with_total_row = True

    counter = 0
    for row in data_tuple:
        if pdf.will_page_break(line_height):
            render_table_header()
        row_height = pdf.font_size * estimate_lines_needed(pdf, row, col_width)
        if row_height < line_height: #min height
            row_height = line_height
        elif row_height > 120: #max height tested, beyond this value will distort the table
            row_height = 120

        if counter % 2 ==0:
            pdf.set_fill_color(222,226,230)
        else:
            pdf.set_fill_color(255,255,255)
        
        if with_total_row and counter + 1 == len(data_tuple):
            border = 'T'
        else:
            border = 0

        column_counter = 0
        for datum in row:
            width = col_width
            if column_counter == 0:
                width = row_number_width
                text_align = 'R'
            else:
                if metadata[header_tuple[column_counter].replace(" ","_")]['data_type'] in ['number', 'date']:
                    text_align = 'R'
                else:
                    text_align = 'L'

            pdf.multi_cell(width, row_height, str(datum), border=border, new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size, fill = True, align = text_align)
            column_counter += 1
        pdf.ln(row_height)
        counter += 1

    return pdf

def render_table_header(pdf, header_tuple, col_width, line_height, row_number_width):
    pdf.set_font(style="B")  # enabling bold text
    pdf.set_fill_color(52, 58,64)
    pdf.set_text_color(255,255,255)
    row_header_line_height = line_height * 1.5
    for col_name in header_tuple:
        if col_name == '#':
            width = row_number_width
        else:
            width = col_width

        pdf.multi_cell(width, row_header_line_height, col_name, border='TB', align='C',
                new_x="RIGHT", new_y="TOP",max_line_height=pdf.font_size, fill=True)
    pdf.ln(row_header_line_height)
    pdf.set_font(style="")  # disabling bold text
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(0, 0, 0)

def render_page_header(pdf, line_height, report_params, pk_field):
    param_width = pdf.epw / 4
    #Report Title
    pdf.set_font("Helvetica", size=14, style="B")
    pdf.multi_cell(0,line_height, "Customer Report", 0, 'C',
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln()

    #Report Parameters
    newline_print_counter = 1
    pdf.set_font("Helvetica", size=12, style="B")
    pdf.multi_cell(0,line_height, "Report Parameters:", 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln(pdf.font_size *1.5)
    if len(report_params) > 0:
        pdf.set_font("Helvetica", size=10)
        for key, value in report_params.items():
            if key == 'pk':
                key = pk_field
            pdf.multi_cell(30,line_height, key.replace("_", " "), 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
            pdf.multi_cell(param_width,line_height, value, 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
            if newline_print_counter == 2:
                pdf.ln(pdf.font_size *1.5)
                newline_print_counter = 0
            newline_print_counter += 1
    else:
        pdf.multi_cell(30,line_height, "N/A", 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln()


def estimate_lines_needed(self, iter, col_width: float) -> int:
    font_width_in_mm = (
        self.font_size_pt * 0.33 * 0.6
    )  # assumption: a letter is half his height in width, the 0.5 is the value you want to play with
    max_cell_text_len_header = max([len(str(col)) for col in iter])  # how long is the longest string?
    return math.ceil(max_cell_text_len_header * font_width_in_mm / col_width)
