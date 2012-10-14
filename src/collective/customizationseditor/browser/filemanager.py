import json
import os
import os.path

from Products.Five.browser.decode import processInputs
from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors import property
from zope.i18n import translate

from plone.resourceeditor.browser import FileManager as Base
from plone.resourceeditor.browser import validateFilename

from collective.customizationseditor.interfaces import CUSTOMIZATIONS_PACKAGE_NAMESPACE

_ = MessageFactory(u"plone")

# TODO: Implement the various operations below


class FileManager(Base):
    """A version of the @@plone.resourceeditor.filemanager API that works with
    filesystem files
    """

    @property.Lazy
    def resourceType(self):
        return CUSTOMIZATIONS_PACKAGE_NAMESPACE

    @property.Lazy
    def resourceDirectory(self):
        return self.context

    @property.Lazy
    def baseUrl(self):
        return "%s/++%s++%s" % (self.portalUrl, self.resourceType, self.resourceDirectory.__name__)

    def getFolder(self, path, getSizes=False):
        """Returns a dict of file and folder objects representing the
        contents of the given directory (indicated by a "path" parameter). The
        values are dicts as returned by getInfo().

        A boolean parameter "getsizes" indicates whether image dimensions
        should be returned for each item. Folders should always be returned
        before files.

        Optionally a "type" parameter can be specified to restrict returned
        files (depending on the connector). If a "type" parameter is given for
        the HTML document, the same parameter value is reused and passed
        to getFolder(). This can be used for example to only show image files
        in a file system tree.
        """

        path = path.encode('utf-8')

        folders = []
        files = []

        path = self.normalizePath(path)
        # folder = self.getObject(path)

        # for name in folder.listDirectory():
        #     if IResourceDirectory.providedBy(folder[name]):
        #         folders.append(self.getInfo(
        #             path="%s/%s/" % (path, name), getSize=getSizes))
        #     else:
        #         files.append(self.getInfo(
        #             path="%s/%s" % (path, name), getSize=getSizes))
        return folders + files

    def getInfo(self, path, getSize=False):
        """Returns information about a single file. Requests
        with mode "getinfo" will include an additional parameter, "path",
        indicating which file to inspect. A boolean parameter "getsize"
        indicates whether the dimensions of the file (if an image) should be
        returned.
        """

        path = path.encode('utf-8')

        path = self.normalizePath(path)
        obj = self.getObject(path)

        filename = obj.__name__
        error = ''
        errorCode = 0

        properties = {
            'dateCreated': None,
            'dateModified': None,
        }

        # if isinstance(obj, File):
        #     properties['dateCreated'] = obj.created().strftime('%c')
        #     properties['dateModified'] = obj.modified().strftime('%c')
        #     size = obj.get_size() / 1024
        #     if size < 1024:
        #         size_specifier = u'kb'
        #     else:
        #         size_specifier = u'mb'
        #         size = size / 1024
        #     properties['size'] = '%i%s' % (size,
        #         translate(_(u'filemanager_%s' % size_specifier, default=size_specifier), context=self.request)
        #         )

        fileType = 'txt'

        siteUrl = self.portalUrl
        # resourceName = self.resourceDirectory.__name__

        preview = "%s/%s/images/fileicons/default.png" % (siteUrl, self.staticFiles)

        # if IResourceDirectory.providedBy(obj):
        #     preview = "%s/%s/images/fileicons/_Open.png" % (siteUrl,
        #                                                     self.staticFiles)
        #     fileType = 'dir'
        #     path = path + '/'
        # else:
        #     fileType = self.getExtension(path, obj)
        #     if fileType in self.imageExtensions:
        #         preview = '%s/++%s++%s/%s' % (siteUrl, self.resourceType,
        #                                       resourceName, path)
        #     elif fileType in self.extensionsWithIcons:
        #         preview = "%s/%s/images/fileicons/%s.png" % (siteUrl,
        #                                                      self.staticFiles,
        #                                                      fileType)

        # if getSize and isinstance(obj, Image):
        #     properties['height'] = obj.height
        #     properties['width'] = obj.width

        return {
            'path': self.normalizeReturnPath(path),
            'filename': filename,
            'fileType': fileType,
            'preview': preview,
            'properties': properties,
            'error': error,
            'code': errorCode,
        }

    def addFolder(self, path, name):
        """Create a new directory on the server within the given path.
        """

        path = path.encode('utf-8')
        name = name.encode('utf-8')

        code = 0
        error = ''

        parentPath = self.normalizePath(path)
        parent = None

        try:
            parent = self.getObject(parentPath)
        except KeyError:
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if not validateFilename(name):
                error = translate(_(u'filemanager_invalid_foldername',
                                  default=u"Invalid folder name."),
                                  context=self.request)
                code = 1
            elif name in parent:
                error = translate(_(u'filemanager_error_folder_exists',
                                  default=u"Folder already exists."),
                                  context=self.request)
                code = 1
            # else:
            #     try:
            #         parent.makeDirectory(name)
            #     except UnicodeDecodeError:
            #         error = translate(_(u'filemanager_invalid_foldername',
            #                       default=u"Invalid folder name."),
            #                       context=self.request)
            #         code = 1

        return {
            'parent': self.normalizeReturnPath(parentPath),
            'name': name,
            'error': error,
            'code': code,
        }

    def add(self, path, newfile, replacepath=None):
        """Add the uploaded file to the specified path. Unlike
        the other methods, this method must return its JSON response wrapped in
        an HTML <textarea>, so the MIME type of the response is text/html
        instead of text/plain. The upload form in the File Manager passes the
        current path as a POST param along with the uploaded file. The response
        includes the path as well as the name used to store the file. The
        uploaded file's name should be safe to use as a path component in a
        URL, so URL-encoded at a minimum.
        """

        path = path.encode('utf-8')
        if replacepath != None:
            replacepath = replacepath.encode('utf-8')

        parentPath = self.normalizePath(path)

        error = ''
        code = 0

        name = newfile.filename
        if isinstance(name, unicode):
            name = name.encode('utf-8')

        if replacepath:
            newPath = replacepath
            parentPath = '/'.join(replacepath.split('/')[:-1])
        else:
            newPath = "%s/%s" % (parentPath, name,)

        try:
            parent = self.getObject(parentPath)
        except KeyError:
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if name in parent and not replacepath:
                error = translate(_(u'filemanager_error_file_exists',
                                  default=u"File already exists."),
                                  context=self.request)
                code = 1
            # else:
            #     try:
            #         self.resourceDirectory.writeFile(newPath, newfile)
            #     except ValueError:
            #         error = translate(_(u'filemanager_error_file_invalid',
            #                           default=u"Could not read file."),
            #                           context=self.request)
            #         code = 1

        return {
            "parent": self.normalizeReturnPath(parentPath),
            "path": self.normalizeReturnPath(path),
            "name": name,
            "error": error,
            "code": code,
        }

    def addNew(self, path, name):
        """Add a new empty file in the given directory
        """
        path = path.encode('utf-8')
        name = name.encode('utf-8')

        error = ''
        code = 0

        # parentPath = self.normalizePath(path)
        newPath = os.path.join(path, name)

        try:
            os.stat(path)
        except OSError:
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if not validateFilename(name):
                error = translate(_(u'filemanager_invalid_filename',
                                  default=u"Invalid file name."),
                                  context=self.request)
                code = 1
            elif name in os.listdir(path):
                error = translate(_(u'filemanager_error_file_exists',
                                  default=u"File already exists."),
                                  context=self.request)
                code = 1
            else:
                opened_file = open(newPath, 'w')
                opened_file.close()

        return {
            "parent": self.normalizeReturnPath(path),
            "name": name,
            "error": error,
            "code": code,
        }

    def rename(self, path, newName):
        """Rename the item at the given path to the new name
        """

        path = path.encode('utf-8')
        newName = newName.encode('utf-8')

        npath = self.normalizePath(path)
        oldPath = newPath = '/'.join(npath.split('/')[:-1])
        oldName = npath.split('/')[-1]

        code = 0
        error = ''

        try:
            parent = self.getObject(oldPath)
        except KeyError:
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if newName != oldName:
                if newName in parent:
                    error = translate(_(u'filemanager_error_file_exists',
                                  default=u"File already exists."),
                                  context=self.request)
                    code = 1
                # else:
                #     parent.rename(oldName, newName)

        return {
            "oldParent": self.normalizeReturnPath(oldPath),
            "oldName": oldName,
            "newParent": self.normalizeReturnPath(newPath),
            "newName": newName,
            'error': error,
            'code': code,
        }

    def delete(self, path):
        """Delete the item at the given path.
        """

        path = path.encode('utf-8')

        npath = self.normalizePath(path)
        parentPath = '/'.join(npath.split('/')[:-1])
        name = npath.split('/')[-1]
        code = 0
        error = ''

        try:
            parent = self.getObject(parentPath)
        except KeyError:
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        # else:
        #     try:
        #         del parent[name]
        #     except KeyError:
        #         error = translate(_(u'filemanager_error_file_not_found',
        #                           default=u"File not found."),
        #                           context=self.request)
        #         code = 1

        return {
            'path': self.normalizeReturnPath(path),
            'error': error,
            'code': code,
        }

    def move(self, path, directory):
        """Move the item at the given path to a new directory
        """

        path = path.encode('utf-8')
        directory = directory.encode('utf-8')

        npath = self.normalizePath(path)
        newParentPath = self.normalizePath(directory)

        parentPath = self.parentPath(npath)
        filename = npath.split('/')[-1]

        code = 0
        error = ''

        try:
            parent = self.getObject(parentPath)
            target = self.getObject(newParentPath)
        except KeyError:
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if filename not in parent:
                error = translate(_(u'filemanager_error_file_not_found',
                                  default=u"File not found."),
                                  context=self.request)
                code = 1
            elif filename in target:
                error = translate(_(u'filemanager_error_file_exists',
                                  default=u"File already exists."),
                                  context=self.request)
                code = 1
            # else:
            #     obj = parent[filename]
            #     del parent[filename]
            #     target[filename] = obj

        newCanonicalPath = "%s/%s" % (newParentPath, filename)

        return {
            'code': code,
            'error': error,
            'newPath': self.normalizeReturnPath(newCanonicalPath),
        }

    def download(self, path):
        """Serve the requested file to the user
        """

        path = path.encode('utf-8')

        npath = self.normalizePath(path)
        parentPath = '/'.join(npath.split('/')[:-1])
        name = npath.split('/')[-1]

        parent = self.getObject(parentPath)

        self.request.response.setHeader('Content-Type',
                                        'application/octet-stream')
        self.request.response.setHeader('Content-Disposition',
                                        'attachment; filename="%s"' % name)

        # return parent.readFile(name)
        return ''

    # Helpers
    def getObject(self, path):
        path = self.normalizePath(path)
        if not path:
            return self.resourceDirectory
        # try:
        #     return self.resourceDirectory[path]
        # except (KeyError, NotFound,):
        #     raise KeyError(path)

    # def getExtension(self, path):
    #     basename, ext = os.path.splitext(path)
    #     ext = ext[1:].lower()

    #     ct = obj.getContentType()
    #     if ct:
    #         # take content type of the file over extension if available
    #         if '/' in ct:
    #             _ext = ct.split('/')[1].lower()
    #         if _ext in self.extensionsWithIcons:
    #             return _ext
    #     return ext

    # Methods that are their own views
    def getFile(self, path):
        self.setup()

        path = path.encode('utf-8')

        # XXX: We'll need this later
        # path = self.normalizePath(path)

        basename, ext = os.path.splitext(path)
        ext = ext[1:].lower()

        result = {'ext': ext}

        # XXX: We need this ?
        # if ext in self.knownExtensions:
        #     result['contents'] = str(file.data)
        # else:
        #     info = self.getInfo(path)
        #     result['info'] = self.previewTemplate(info=info)

        opened_file = open(path, 'r')
        result['contents'] = str(opened_file.read())
        opened_file.close()

        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    def saveFile(self, path, value):
        path = path.encode('utf-8')

        # XXX: We need this ?
        # processInputs(self.request)

        value = value.replace('\r\n', '\n')

        opened_file = open(path, 'w')
        opened_file.write(value.encode('utf-8'))
        opened_file.close()

        return ' '  # Zope no likey empty responses

    def filetree(self):

        foldersOnly = bool(self.request.get('foldersOnly', False))

        def getFolder(root):
            result = []
            for name in os.listdir(root):
                path = os.path.join(root, name)
                if os.path.isdir(path):
                    item = {
                        'title': name,
                        'key': path,
                        'isFolder': True
                    }
                    item['children'] = getFolder(path)
                    result.append(item)
                elif not foldersOnly:
                    item = {
                        'title': name,
                        'key': path,
                        'isFolder': False
                    }
                    result.append(item)
            return result
        return json.dumps([{
            'title': '/',
            'key': '/',
            'isFolder': True,
            "expand": True,
            'children': getFolder(self.context.path)
        }])
