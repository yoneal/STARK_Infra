#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

def create(data):

    project_name = data["Project Name"]

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
            <script src="js/STARK_home.js" defer></script>

            <title>{project_name}</title>
        </head>
        <body class="bg-light">
        <div class="container-fluid" id="vue-root">

            <div class="row bg-primary mb-3 p-3 text-white" style="background-image: url('images/banner_generic_blue.png')">
                <div class="col">
                <h2>
                    {project_name}
                </h2>
                </div>
            </div>

            <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
                <li class="breadcrumb-item active" aria-current="page">Home</li>
            </ol>
            </nav>

            <div class="modules_list_box">
                <div class="row" id="modules_list">
                    <template v-for="module in modules" id="modules-template">
                        <div class="col">
                            <div class="card mb-3 p-2 module_card" :onclick="'window.location.href=\\''  + module.href + '\\''">
                                <img class="card-img-top" :src="module.image" :alt="module.image_alt">
                                <div class="card-body">
                                    <h5 class="card-title">{{{{ module.title }}}}</h5>
                                    <p class="card-text">{{{{ module.description }}}}</p>
                                    <a href="#" class="btn btn-primary w-100">Go</a>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

        </div>

        <div class="d-flex justify-content-center" id="loading-spinner" :style="{{visibility: visibility}}">
            <div class="spinner-border" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        </div>
        </body>
        </html>"""

    return textwrap.dedent(source_code)