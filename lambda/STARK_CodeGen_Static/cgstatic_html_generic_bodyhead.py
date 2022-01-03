#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data, breadcrumb):

    project = data["Project Name"]
    entity  = data["Entity"]

    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)

    source_code = f"""\
        <body class="bg-light">
        <div class="container-fluid">

            <div class="row bg-primary mb-3 p-3 text-white" style="background-image: url('images/banner_generic_blue.png')">
                <div class="col-12 col-md-10">
                <h2>
                    {project}
                </h2>
                </div>
                <div class="col-12 col-md-2 text-right">
                    <b-button 
                        v-b-tooltip.hover title="Log out"
                        class="mt-3" 
                        variant="light" 
                        size="sm">
                        <img src="images/logout.png" height="20px">
                    </b-button>
                </div>
            </div>

            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="home.html">Home</a></li>
                    <li class="breadcrumb-item"><a href="{entity_varname}.html">{entity}</a></li>
                    <li class="breadcrumb-item active" aria-current="page">{breadcrumb}</li>
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

"""

    return source_code
