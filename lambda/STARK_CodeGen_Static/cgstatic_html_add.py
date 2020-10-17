#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import cgstatic_relationships as cg_rel
import cgstatic_controls_coltype as cg_coltype
import convert_friendly_to_system as converter

def create(data):

    project = data["Project Name"]
    entity  = data["Entity"]
    cols    = data["Columns"]
    pk      = data["PK"]

    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)
    pk_varname = converter.convert_to_system_name(pk)

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
            <script src="js/STARK.js" defer></script>
            <script src="js/STARK_spinner.js" defer></script>
            <script src="js/STARK_loading_modal.js" defer></script>
            <script src="js/{entity_varname}_app.js" defer></script>
            <script src="js/{entity_varname}_view.js" defer></script>"""

    #Figure out which other _app.js files we need to add based on relationships
    for col, col_type in cols.items():
        entities = cg_rel.get({
            "col": col,
            "col_type": col_type,
        })
    
    for related in entities:
        related_varname = converter.convert_to_system_name(related)
        source_code = f"""
            <script src="js/{related_varname}_app.js" defer></script>"""

    

    source_code = f"""
            <script src="js/generic_root_get.js" defer></script>

            <title>{project} - {entity}</title>
        </head>
        <body class="bg-light">
        <div class="container-fluid">

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
                    <li class="breadcrumb-item"><a href="{entity_varname}.html">{entity}</a></li>
                    <li class="breadcrumb-item active" aria-current="page">New</li>
                </ol>
            </nav>
        </div>

        <div>
            <b-modal id="loading-modal"
                no-close-on-backdrop
                no-close-on-esc
                hide-header
                hide-footer
                centered
                size="sm">
                <div class="text-center p-3">
                    <div class="spinner-border" style="width: 5rem; height: 5rem" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <div class="mt-3">
                        Loading...
                    </div>
                </div>
            </b-modal>
        </div>

        <div class="container hidden" id="vue-root" :style="{{visibility: visibility}}">
            <div class="row">
                <div class="col">
                    <div class="my-auto">
                        <form class="border p-3">
                        <input type="hidden" id="orig_{pk_varname}" v-model="{entity_varname}.{pk_varname}">
                        <div class="form-group">
                            <label for="{pk_varname}">{pk}</label>
                            <input type="text" class="form-control" id="{pk_varname}" placeholder="" v-model="{entity_varname}.{pk_varname}">
                        </div>"""

    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        html_control_code = cg_coltype.create({
            "col": col,
            "col_type": col_type,
            "col_varname": col_varname,
            "entity" : entity,
            "entity_varname": entity_varname
        })

        source_code += f"""
                        <div class="form-group">
                            <label for="{col_varname}">{col}</label>
                            {html_control_code}
                        </div>"""

    source_code += f"""\
                        <button type="button" class="btn btn-secondary" onClick="window.location.href='{entity_varname}.html'">Back</button>
                        <button type="button" class="btn btn-primary float-right" onClick="root.add()">Add</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        </body>
        </html>
    """

    return textwrap.dedent(source_code)
