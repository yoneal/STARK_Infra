#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

#Private modules
import cgstatic_controls_coltype as cg_coltype
import convert_friendly_to_system as converter

def create(data):

    entity = data["Entity"]
    cols   = data["Columns"]
    pk     = data['PK']

    entity_varname = converter.convert_to_system_name(entity)
    entity_app     = entity_varname + '_app'
    pk_varname     = converter.convert_to_system_name(pk)

    source_code = f"""\
        var {entity_app} = {{
            
            api_endpoint: STARK.{entity_varname},

            add: function (payload) {{
                fetchUrl = this.api_endpoint
                return STARK.request('POST', fetchUrl, payload)
            }},

            delete: function (payload) {{
                fetchUrl = this.api_endpoint
                return STARK.request('DELETE', fetchUrl, payload)
            }},

            update: function (payload) {{
                fetchUrl = this.api_endpoint
                return STARK.request('PUT', fetchUrl, payload)
            }},

            get: function (data) {{
                fetchUrl = this.api_endpoint + '?rt=detail&{pk_varname}=' + data['{pk_varname}']
                return STARK.request('GET', fetchUrl)
            }},

            list: function () {{
                fetchUrl = this.api_endpoint + '?rt=all'
                return STARK.request('GET', fetchUrl)
            }},
        }}

    """

    return textwrap.dedent(source_code)