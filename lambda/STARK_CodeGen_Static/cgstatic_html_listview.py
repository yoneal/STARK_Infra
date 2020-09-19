#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap

def create(data):

    project = data["Project Name"]
    entity  = data["Entity"]
    cols    = data["Columns"]
    pk      = data["PK"]

    #Convert human-friendly names to variable-friendly names
    entity_varname = entity.replace(" ", "_").lower()
    pk_varname = entity.replace(" ", "_").lower()

    source_code = f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <meta http-equiv="content-type" content="text/html; charset=UTF-8" />

            <link rel="stylesheet" href="css/bootstrap.min.css" />
            <link rel="stylesheet" href="css/bootstrap-vue.css" />
            <link rel="stylesheet" href="css/STARK.css" />

            <script src="js/vue.js" defer></script>
            <script src="js/bootstrap-vue.min.js" defer></script>
            <script src="js/STARK_settings.js" defer></script>
            <script src="js/STARK_spinner.js" defer></script>
            <script src="js/STARK_loading_modal.js" defer></script>
            <script src="js/{entity_varname}.js" defer></script>
            <script src="js/generic_root_list.js" defer></script>

            <title>{project} - {entity}</title>
        </head>
        <body class="bg-light">
        <div class="container-fluid" id="vue-root">

            <div class="row bg-primary mb-3 p-3 text-white" style="background-image: url('images/banner_generic_blue.png')">
                <div class="col">
                <h2>
                    {project}
                </h2>
                </div>
            </div>

            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="index.html">Home</a></li>
                    <li class="breadcrumb-item active" aria-current="page">{entity}</li>
                </ol>
            </nav>


            <!-- 
                Empty because this isn't used by the ListView page by default, but the stub is needed so that VueJS won't complain about 
                the loading modal reference in our shared JS library that backs this module
            -->
            <div>
                <b-modal id="loading-modal"
                    no-close-on-backdrop
                    no-close-on-esc
                    hide-header
                    hide-footer
                    centered
                    size="sm">
                </b-modal>
            </div>
            
            <button type="button" class="btn btn-primary mb-2" onClick="window.location.href='{entity_varname}_add.html'"> <b>+</b> Add </button>
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
                                <tr class>
                                    <td>
                                        <a :href="'{entity_varname}_edit.html?{pk_varname}=' + {entity_varname}.{pk_varname}"><img src="images/pencil2.png"></a>
                                    </td>
                                    <th scope="row"><a :href="'{entity_varname}_view.html?{pk_varname}=' + {entity_varname}.{pk_varname}">{{{{ {entity_varname}.{pk_varname} }}}}</a></th>"""

    for col in cols:
        col_varname = col.replace(" ", "_").lower()
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

        <div class="d-flex justify-content-center" id="loading-spinner" :style="{{visibility: visibility}}">
            <div class="spinner-border" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        </div>

        </body>
        </html>
    """

    return textwrap.dedent(source_code)