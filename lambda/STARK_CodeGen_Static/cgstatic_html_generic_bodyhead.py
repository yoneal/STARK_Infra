#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data, breadcrumb):

    project = data["Project Name"]
    
    if breadcrumb != "_HomePage":
        entity  = data["Entity"]
        #Convert human-friendly names to variable-friendly names
        entity_varname = converter.convert_to_system_name(entity)

    source_code = f"""\
        <body class="bg-light">
        <div class="container-fluid" id="vue-root">

            <div class="row bg-primary mb-3 p-3 text-white" style="background-image: url('images/banner_generic_blue.png')">
                <div class="col-12 col-md-10">
                <h2>
                    {project}
                </h2>
                </div>
                <div class="col-12 col-md-2 text-right">
                    <b-button 
                        v-b-tooltip.hover title="Settings"
                        class="mt-3" 
                        variant="light" 
                        size="sm">
                        <img src="images/settings.png" height="20px">
                    </b-button>
                    <b-button 
                        v-b-tooltip.hover title="Log out"
                        class="mt-3" 
                        variant="light" 
                        size="sm"
                        onClick="STARK.logout()">
                        <img src="images/logout.png" height="20px">
                    </b-button>
                </div>
            </div>
"""
    if breadcrumb == "_Listview":
        source_code += f"""\
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="home.html">Home</a></li>
                    <li class="breadcrumb-item active" aria-current="page">{entity}</li>
                </ol>
            </nav>

"""
    elif breadcrumb == "_HomePage":
        source_code += f"""\
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item active" aria-current="page">Home</li>
                </ol>
            </nav>

"""
    else:
        source_code += f"""\
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="home.html">Home</a></li>
                    <li class="breadcrumb-item"><a href="{entity_varname}.html">{entity}</a></li>
                    <li class="breadcrumb-item active" aria-current="page">{breadcrumb}</li>
                </ol>
            </nav>

"""

    return source_code
