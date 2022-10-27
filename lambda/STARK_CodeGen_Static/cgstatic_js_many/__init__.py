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
        {entity_varname}: [
            {{
                '{pk_varname}': '',"""
    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                '{col_varname}': '',"""
    source_code += f"""
            }}
        ],

        add_object: {{"""
    source_code += f"""
            '{pk_varname}': '',"""
    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
            '{col_varname}': '',"""

    source_code += f"""
        }}
        
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
        add_field: function (entity) {{
            this.{entity_varname}.push(this.add_object)
        }},
        remove_field: function (index, entity) {{
            this.{entity_varname}.splice(index, 1);       
        }},
        """

    
    source_code += f"""
    }}
    """

    return textwrap.dedent(source_code)