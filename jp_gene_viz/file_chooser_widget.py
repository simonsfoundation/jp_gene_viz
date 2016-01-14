

import os
import traitlets
from jp_gene_viz import js_proxy
from jp_gene_viz import js_context
from IPython.display import display
import urlparse


class FileChooser(traitlets.HasTraits):

    """
    Upload a file and/or choose a file from server side directory.
    Watch the file_path for changes for chosen file.

    XXXX This widget uses "data" URIs to implement the upload feature.
    which may not work for files larger than a few 10s of Megs.
    """

    file_path = traitlets.Unicode("", sync=True)

    verbose = False

    def __init__(self, message="Choose file",
        root=".", files=True, folders=False, upload=False, 
        dialog=True, width=500,
        *args, **kwargs):
        """
        FileChooser constructor.

        Parameters
        ----------
        message : str 
            Message near the top of the widget as a prompt.
        root : str
            The root path for the top folder to display.
        files : bool
            Make non-folders selectable iff true.
        folders : bool
            Show folders iff true.
        upload : bool
            Enable file upload iff true.
        dialog : bool
            Show in a jQueryUI dialog iff true, else inline.
        width : int
            Width of widget in pixels.
        """
        super(FileChooser, self).__init__(*args, **kwargs)
        js_context.load_if_not_loaded(["simple_upload_button.js"])
        js_context.load_if_not_loaded(["server_file_chooser.js"])
        self.root = root
        self.upload = upload
        self.files = files
        self.folders = folders
        self.dialog = dialog
        self.message = message
        self.width = width
        self.widget = js_proxy.ProxyWidget()
        self.layout([self.root])

    def layout(self, path_list, message=""):
        if not message:
            message = self.message
        path = os.path.join(*path_list)
        listing = []
        if not os.path.isdir(path):
            message = "NOT A DIRECTORY!"
        else:
            for filename in os.listdir(path):
                filepath = os.path.join(path, filename)
                if os.path.isdir(filepath):
                    listing.append([filename, "folder"])
                else:
                    listing.append([filename, "file"])
        options = {}
        options["files"] = self.files
        w = self.widget
        select_callback = w.callback(self.handle_select, data=None, level=2)
        upload_callback = None
        if self.upload:
            upload_callback = w.callback(self.handle_upload, data=None, level=2)
        elt = w.element()
        w(elt.empty())
        target = elt
        if self.dialog:
            target = elt.dialog()
            if self.width:
                # initialize the dialog before calling methods
                w(target)
                w(elt.dialog("option", "width", self.width))
                pass
        #w(target.empty())
        if self.width:
            w(target.width(self.width))
        w(elt.server_file_chooser(
            path_list, listing, select_callback, upload_callback, message, options).
            appendTo(target)
        )
        w.flush()

    def handle_select(self, data, args):
        if self.verbose:
            from pprint import pprint
            pprint(("handle_select", args))
        parent_path = args["0"]
        [filename, kind] = args["1"]
        path = parent_path + [filename]
        path_str = os.path.join(*path)
        if kind == "file" and self.files:
            # Set the trait selecting the file
            self.file_path = path_str
        if kind == "folder":
            if self.folders:
                # Set the trait selecting the folder
                self.file_path = path_str
            # open the folder in the widget
            self.layout(path, message="chose folder " + repr(path_str))
        else:
            self.layout(parent_path, message="chose " + repr(path_str))

    def handle_upload(self, data, args):
        # XXX does not check for file exists.
        if self.verbose:
            from pprint import pprint
            pprint(("handle_upload", args))
        parent_path = args["0"]
        file_info = args["1"]
        filename = file_info["name"]
        hexcontent = file_info["hexcontent"]
        path = parent_path + [filename]
        path_str = os.path.join(*path)
        f = open(path_str, "wb")
        #f.write(content)
        #print "hexcontent", hexcontent
        #for i in xrange(0, len(hexcontent), 2):
        #    hexcode = hexcontent[i: i+2]
        #    char = chr(int(hexcode, 16))
        for char in from_hex_iterator(hexcontent):
            f.write(char)
        f.close()
        self.layout(parent_path, message="uploaded " + repr(path_str))

    def download_on_change_callback(self, dummy, filepath):
        """
        Use an URL served by the notebook server to download the file.
        This will only work for files under the folder containing the notebook.

        This method may break if a proxy changes the URL in transit.
        """
        w = self.widget
        window = w.window()
        # eg: http://localhost:8888/notebooks/repos/jp_gene_viz/examples/cytoscape%20js_proxy.ipynb#
        notebook_url = w.evaluate(window.location.href)
        # eg: /notebooks/repos/jp_gene_viz/examples/cytoscape%20js_proxy.ipynb
        notebook_path = urlparse.urlsplit(notebook_url).path
        # eg /notebooks/repos/jp_gene_viz/examples
        folder_path = notebook_path.rsplit("/", 1)[0]
        prefix = "/notebooks/"
        assert folder_path.startswith(prefix), "bad folder " + repr((prefix, folder_path))
        # eg /files/repos/jp_gene_viz/examples
        file_folder = "/files/" + folder_path[len(prefix):]
        (_, filename) = os.path.split(filepath)
        uri = urlparse.urljoin(file_folder + "/", filepath)
        w(window.console.log("Download uri " + repr(uri)))
        print ("Download uri " + repr(uri))
        download = w.element().server_file_chooser.download
        w(download(uri, filename))
        w.flush()

    def download_on_change_callback_base64(self, dummy, filepath):
        """
        Use a "data download link" to download a file from the server.
        WARNING: This method silently fails for files larger than a few megabytes.
        """
        # https://gist.github.com/jbergantine/1171682
        base64 = open(filepath, "rb").read().encode("base64").replace("\n", "")
        uri = "data:x-download/misc;base64," + base64
        (_, filename) = os.path.split(filepath)
        w = self.widget
        download = w.element().server_file_chooser.download
        w(download(uri, filename))
        w.flush()

    def enable_downloads(self):
        self.on_trait_change(self.download_on_change_callback, "file_path")

    def show(self):
        display(self.widget)


def from_hex_iterator(hexcontent):
    for i in xrange(0, len(hexcontent), 2):
        hexcode = hexcontent[i: i+2]
        char = chr(int(hexcode, 16))
        yield char

def from_hex(hexcontent):
    return "".join(list(from_hex_iterator(hexcontent)))

def print_filename(dummy, filename):
    "useful for debugging."
    print ("path chosen callback: " + filename)


def simple_file_downloader(root=".", upload=False):
    "Download file in root or descendant of root."
    chooser = FileChooser(upload=upload, message="download files")
    chooser.enable_downloads()
    chooser.show()
    return chooser

def simple_file_uploader(root="."):
    "Upload to root or existing folder descendant of root."
    chooser = FileChooser(upload=True, files=False, message="upload files")
    chooser.show()
    return chooser
