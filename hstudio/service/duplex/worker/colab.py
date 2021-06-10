from hstudio.utils import format_url

def get_public_addr(port):
    from google.colab.output import eval_js
    addr = eval_js("google.colab.kernel.proxyPort(%d)" % port)
    return format_url(addr)