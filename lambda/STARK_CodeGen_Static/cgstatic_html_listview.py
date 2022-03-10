#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter
import cgstatic_html_generic_header as cg_header
import cgstatic_html_generic_footer as cg_footer
import cgstatic_html_generic_bodyhead as cg_bodyhead
import cgstatic_html_generic_loadingmodal as cg_loadmod
import cgstatic_html_generic_loadingspinner as cg_loadspin

def create(data):

    project = data["Project Name"]
    entity  = data["Entity"]
    cols    = data["Columns"]
    pk      = data["PK"]

    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)
    pk_varname = converter.convert_to_system_name(pk)

    source_code  = cg_header.create(data, "Listview")
    source_code += cg_bodyhead.create(data, "_Listview")

    source_code += f"""\
            <div class="row">
                <div class="col-6">
                    <button type="button" class="btn btn-primary mb-2" onClick="window.location.href='{entity_varname}_add.html'"> <b>+</b> Add </button>
                </div>
                <div class="col-6 text-right d-inline-block">        
                    <button id="prev" type="button" class="btn btn-outline-secondary" :disabled="prev_disabled" onClick="root.list(root.prev_token, 'prev')"> < </button>
                    <button id="next" type="button" class="btn btn-outline-secondary" :disabled="next_disabled" onClick="root.list(root.next_token, 'next')"> > </button>
                </div>
            </div>

            <div class="row">
                <div class="col overflow-auto">
                    <table class="table  table-hover table-striped">
                        <thead class="thead-dark">
                            <tr>
                                <th scope="col">Edit</th>
                                <th scope="col">{pk}</th>"""
    for col in cols:
        source_code += f"""
                                <th scope="col">{col}</th>"""

    source_code += f"""
                                <th scope="col">Del</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="{entity_varname} in listview_table" id="listview-table">
                                <tr>
                                    <td>
                                        <a :href="'{entity_varname}_edit.html?{pk_varname}=' + {entity_varname}.{pk_varname}"><img src="images/pencil2.png"></a>
                                    </td>
                                    <th scope="row"><a :href="'{entity_varname}_view.html?{pk_varname}=' + {entity_varname}.{pk_varname}">{{{{ {entity_varname}.{pk_varname} }}}}</a></th>"""

    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                                    <td>{{{{ {entity_varname}.{col_varname} }}}}</td>"""

    source_code += f"""
                                    <td><a :href="'{entity_varname}_delete.html?{pk_varname}=' + {entity_varname}.{pk_varname}"><img src="images/trash2.png"></a></td>
                                </tr>
                            </template>
                    </tbody>
                    </table>
                </div>
            </div>

        </div>
    """
    source_code += cg_loadspin.create()
    source_code += cg_loadmod.create()
    source_code += cg_footer.create()

    return textwrap.dedent(source_code)
