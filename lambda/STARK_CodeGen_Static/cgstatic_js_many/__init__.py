#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap
import os
import importlib

#Private modules
prepend_dir = ""
if 'libstark' in os.listdir():
    prepend_dir = "libstark.STARK_CodeGen_Static."

cg_coltype = importlib.import_module(f"{prepend_dir}cgstatic_controls_coltype")  
import convert_friendly_to_system as converter

def create(data):
    entity         = data["Entity"]
    cols           = data["Columns"]
    pk             = data['PK']
    relationships  = data["Relationships"]

    entity_varname = converter.convert_to_system_name(entity)
    entity_app     = entity_varname + '_app'
    pk_varname     = converter.convert_to_system_name(pk)

    source_code = f"""\
    many_{entity_varname} = {{
        metadata: {{
            '{pk_varname}': {{
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'S'
            }},"""
    
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        data_type = set_data_type(col_type)
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_many_ux = col_type.get('has_many_ux', None)
            if has_many_ux == None:
                source_code += f"""
            '{col_varname}': {{
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '{data_type}'
            }},""" 
        else:
            source_code += f"""
            '{col_varname}': {{
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '{data_type}'
            }},""" 
                    
    source_code += f"""
        }},

        validation_properties: [
            {{
                '{pk_varname}': {{
                    'state': null,
                    'feedback': ''
                }},"""
    
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        data_type = set_data_type(col_type)
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_many_ux = col_type.get('has_many_ux', None)
            if has_many_ux == None:
                source_code += f"""
                '{col_varname}': {{
                    'state': null,
                    'feedback': ''
                }},""" 
        else:
            source_code += f"""
                '{col_varname}': {{
                    'state': null,
                    'feedback': ''
                }}
            }}
        ],
    
        module_fields: [
            {{
                '{pk_varname}': '',"""
    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                '{col_varname}': '',"""
    source_code += f"""
            }}
        ],
        
        list_status: {{"""

    for col, col_type in cols.items():
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_one = col_type.get('has_one', '')
            if  has_one != '':
                foreign_entity  = converter.convert_to_system_name(has_one)
                source_code += f"""
            '{foreign_entity}': 'empty',"""

    source_code += f"""
        }},
    """

    for col, col_type in cols.items():
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_one = col_type.get('has_one', '')
            if  has_one != '':
                foreign_entity  = converter.convert_to_system_name(has_one)
                foreign_field   = converter.convert_to_system_name(col_type.get('value', foreign_entity))
                foreign_display = converter.convert_to_system_name(col_type.get('display', foreign_field))

                source_code += f"""
        list_{foreign_entity}: function () {{
            if (many_Order_Items.list_status.{foreign_entity} == 'empty') {{
                loading_modal.show();
                root.lists.{foreign_entity} = []

                fields = ['{foreign_field}', '{foreign_display}']
                {foreign_entity}_app.get_fields(fields).then( function(data) {{
                    data.forEach(function(arrayItem) {{
                        value = arrayItem['{foreign_field}']
                        text  = arrayItem['{foreign_display}']"""
                    
                source_code += f"""            
                    root.lists.{foreign_entity}.push({{ value: value, text: text }})"""
                
                source_code += f""" 
                    }})
                    many_Order_Items.list_status.{foreign_entity} = 'populated'
                    loading_modal.hide();
                }}).catch(function(error) {{
                    console.log("Encountered an error! [" + error + "]")
                    loading_modal.hide();
                }});
            }}
        }},

        many_validation() {{
            is_valid_form = true
            for (let index = 0; index < this.module_fields.length; index++) {{
                console.log(this.module_fields[index])
                response = STARK.validate_form(this.metadata, this.module_fields[index])
                this.validation_properties[index] = response['validation_properties']
                if (response['is_valid_form'] == false)
                {{
                    is_valid_form = false
                }}
            }}
            return is_valid_form
        }},

        add_field: function (param='') {{

            var new_row = {{"""
    source_code += f"""
                '{pk_varname}': '',"""
    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                '{col_varname}': '',"""
    source_code += f"""
            }}

            var validation_properties = {{
                '{pk_varname}': {{
                    'state': null,
                    'feedback': ''
                }},"""
    
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        data_type = set_data_type(col_type)
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_many_ux = col_type.get('has_many_ux', None)
            if has_many_ux == None:
                source_code += f"""
                '{col_varname}': {{
                    'state': null,
                    'feedback': ''
                }},""" 
        else:
            source_code += f"""
                '{col_varname}': {{
                    'state': null,
                    'feedback': ''
                }}
            }},

            if(param != '') {{
                new_row = param
            }}

            this.module_fields.push(new_row)
            this.validation_properties.push(validation_properties)
        }},
        
        remove_field: function (index) {{
            this.module_fields.splice(index, 1);       
            this.validation_properties.splice(index, 1);       
        }},  
        """

    
    source_code += f"""
    }}
    """

    return textwrap.dedent(source_code)

def set_data_type(col_type):

    #Default is 'S'. Defined here so we don't need duplicate Else statements below
    data_type = 'String'

    if isinstance(col_type, dict):
        #special/complex types
        if col_type["type"] in [ "int-spinner" ]:
            data_type = 'Number'

        if col_type["type"] in [ "decimal-spinner" ]:
            data_type = 'Float'
        
        if col_type["type"] in [ "tags", "multiple choice" ]:
            data_type = 'List'
    
    elif col_type in [ "int", "number" ]:
        data_type = 'Number'

    return data_type