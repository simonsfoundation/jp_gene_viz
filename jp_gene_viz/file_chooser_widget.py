

import os
import traitlets
from jp_gene_viz import js_proxy
from jp_gene_viz import js_context
from IPython.display import display


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
        dialog=True, *args, **kwargs):
        super(FileChooser, self).__init__(*args, **kwargs)
        js_context.load_if_not_loaded(["simple_upload_button.js"])
        js_context.load_if_not_loaded(["server_file_chooser.js"])
        self.root = root
        self.upload = upload
        self.files = files
        self.folders = folders
        self.dialog = dialog
        self.message = message
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
        target = elt
        if self.dialog:
            target = elt.dialog()
        w(target.empty())
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
        for i in xrange(0, len(hexcontent), 2):
            hexcode = hexcontent[i: i+2]
            char = chr(int(hexcode, 16))
            f.write(char)
        f.close()
        self.layout(parent_path, message="uploaded " + repr(path_str))

    def download_on_change_callback(self, dummy, filepath):
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
