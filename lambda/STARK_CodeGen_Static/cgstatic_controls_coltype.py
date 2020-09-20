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

    elif isinstance(col_type, dict):
        #These are the complex data types that need additional settings as part of their spec
        #   All col_type dicts follow this format:
        #       { "type": "columntype", "type-specific attrib1": "value", "type-specific attrib2": "value" }
        #   Only the "type" index is fixed. All the other indexes may vary depending on the column type specified

        #Spinbutton - useful as a user-friendly int chooser. 
        #   Can also be transformed to a generic string chooser, as long as the internal value is mapped to integers
        #       We should probably handle that as a different col type, though
        if col_type["type"] == "int-spinner" or col_type["type"] == "decimal-spinner":

            spin_wrap = "wrap"
            spin_min  = 0

            if col_type["type"] == "int-spinner":
                spin_step = 1
                spin_max  = 99
            else:
                spin_step = 0.1
                spin_max  = 10
            
            if int(col_type.get('min', 0)) != 0:
                spin_min = int(col_type.get('min'))

            if int(col_type.get('max', 0)) != 0:
                spin_max = int(col_type.get('max'))

            if float(col_type.get('spin_step', 0)) != 0:
                spin_step = float(col_type.get('spin_step', 0))

            if col_type.get('wrap','') == "no-wrap":
                spin_wrap = ""

            html_code=f"""<b-form-spinbutton class="mb-2" id="{col_varname}" v-model="{entity_varname}.{col_varname}" {spin_wrap} min="{spin_min}" max="{spin_max}" step="{spin_step}">"""




    else:
        html_code=f"""<input type="text" class="form-control" id="{col_varname}" placeholder="" v-model="{entity_varname}.{col_varname}">"""


                      

    return html_code