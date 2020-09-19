#STARK Code Generator component.
#Produces HTML code for different controls, depending on column type

#Python Standard Library
import base64
import textwrap

def create(data):

    col             = data['col']
    col_type        = data['col_type']
    col_varname     = data['col_varname']
    entity          = data['entity']
    entity_varname  = data['entity_varname']
    html_code       = ""

    if isinstance(col_type, str):
        col_type = col_type.lower()

    if col_type == "date":
        html_code=f"""<b-form-datepicker id="{col_varname}" show-decade-nav v-model="{entity_varname}.{col_varname}" class="mb-2"></b-form-datepicker>"""

    elif col_type == "multi-line-string":
        html_code=f"""<textarea class="form-control" id="{col_varname}" v-model="{entity_varname}.{col_varname}" placeholder="" rows="4"></textarea>"""

    elif isinstance(col_type, list):
        html_code=f"""<select class="form-control" id="{col_varname}" v-model="{entity_varname}.{col_varname}">
                                <option disabled value="">Please select one</option>"""
        for item in col_type:
            html_code+=f"""
                                <option>{item}</option>"""
        html_code+=f"""
                            </select>"""

    else:
        html_code=f"""<input type="text" class="form-control" id="{col_varname}" placeholder="" v-model="{entity_varname}.{col_varname}">"""


                      

    return html_code