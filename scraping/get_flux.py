import gdown
def import_flux():
    url = "https://drive.google.com/uc?id=1JiYTXHsWs7nvn6_w5aPP6euFfWqP0WnG"
    output = "flux.zip"
    gdown.download(url, output, quiet=False)
    return "ok"