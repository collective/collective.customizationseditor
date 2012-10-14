import json
import os
import os.path
import time
import shutil

from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors import property
from zope.i18n import translate

from plone.resourceeditor.browser import FileManager as Base
from plone.resourceeditor.browser import validateFilename

from collective.customizationseditor.interfaces import CUSTOMIZATIONS_PACKAGE_NAMESPACE

from zExceptions import Unauthorized

_ = MessageFactory(u"plone")

# TODO: Implement the various operations below


class FileManager(Base):
    """A version of the @@plone.resourceeditor.filemanager API that works with
    filesystem files
    """

    ignoredExtensions = ['pyc', 'pyo']

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

        absolutePath = self.getAbsolutePath(path)

        folders = []
        files = []

        for name in os.listdir(absolutePath):
            if self.getExtension(name) not in self.ignoredExtensions:
                itemPath = os.path.join(absolutePath, name)
                if os.path.isdir(itemPath):
                    folders.append(self.getInfo(path=os.path.join(path, name), getSize=getSizes))
                else:
                    files.append(self.getInfo(path=os.path.join(path, name), getSize=getSizes))
        return folders + files

    def getInfo(self, path, getSize=False):
        """Returns information about a single file. Requests
        with mode "getinfo" will include an additional parameter, "path",
        indicating which file to inspect. A boolean parameter "getsize"
        indicates whether the dimensions of the file (if an image) should be
        returned.
        """

        absolutePath = self.getAbsolutePath(path)
        filename = self.getFilename(absolutePath)
        error = ''
        errorCode = 0

        properties = {
            'dateCreated': None,
            'dateModified': None,
        }

        if os.path.isfile(absolutePath):
            properties['dateCreated'] = time.ctime(os.path.getctime(absolutePath))
            properties['dateModified'] = time.ctime(os.path.getmtime(absolutePath))
            size = os.path.getsize(absolutePath) / 1024
            if size < 1024:
                size_specifier = u'kb'
            else:
                size_specifier = u'mb'
                size = size / 1024
            properties['size'] = '%i%s' % (size,
                translate(_(u'filemanager_%s' % size_specifier, default=size_specifier), context=self.request)
                )

        fileType = 'txt'

        siteUrl = self.portalUrl
        preview = "%s/%s/images/fileicons/default.png" % (siteUrl, self.staticFiles)

        if os.path.isdir(absolutePath):
            preview = "%s/%s/images/fileicons/_Open.png" % (siteUrl, self.staticFiles)
            fileType = 'dir'
            path = path + '/'
        else:
            fileType = self.getExtension(absolutePath)
            if fileType in self.extensionsWithIcons:
                preview = "%s/%s/images/fileicons/%s.png" % (siteUrl,
                                                             self.staticFiles,
                                                             fileType)
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
        """Create a new directory in the filesystem within the given path.
        """
        path = path.encode('utf-8')
        name = name.encode('utf-8')

        code = 0
        error = ''

        absolutePath = self.getAbsolutePath(path)

        newPath = os.path.join(absolutePath, name)

        if not os.path.isdir(absolutePath):
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
            elif os.path.exists(newPath):
                error = translate(_(u'filemanager_error_folder_exists',
                                  default=u"Folder already exists."),
                                  context=self.request)
                code = 1
            else:
                try:
                    os.mkdir(newPath)
                except OSError, e:
                    if e.errno == 13:
                        error = translate(_(u'filemanager_error_unauthorized',
                                  default=(u"You are not allowed to create a "
                                            "folder in \"%s\"." % path)),
                                  context=self.request)
                        code = 1

                    else:
                        error = translate(_(u'filemanager_error_unknown',
                                  default=(u"Something bad happened: "
                                            "\"%s\"." % e.strerror)),
                                  context=self.request)
                        code = 1

        return {
            'parent': self.normalizeReturnPath(path),
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

        parentPath = self.getAbsolutePath(path)

        error = ''
        code = 0

        name = newfile.filename
        if isinstance(name, unicode):
            name = name.encode('utf-8')

        if replacepath:
            newPath = replacepath
            parentPath = '/'.join(replacepath.split('/')[:-1])
        else:
            newPath = os.path.join(parentPath, name)

        if not os.path.exists(parentPath):
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if os.path.exists(newPath) and not replacepath:
                error = translate(_(u'filemanager_error_file_exists',
                                  default=u"File already exists."),
                                  context=self.request)
                code = 1
            else:
                openedFile = open(newPath, 'wb')
                openedFile.write(newfile.read())
                openedFile.close()

        return {
            "parent": self.normalizeReturnPath(path),
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

        absolutePath = self.getAbsolutePath(path)

        error = ''
        code = 0

        newPath = os.path.join(absolutePath, name)

        if not os.path.isdir(absolutePath):
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
            elif os.path.exists(newPath):
                error = translate(_(u'filemanager_error_file_exists',
                                  default=u"File already exists."),
                                  context=self.request)
                code = 1
            else:
                openedFile = open(newPath, 'w')
                openedFile.close()

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

        absolutePath = self.getAbsolutePath(path)

        oldPath, oldName = os.path.split(absolutePath)

        code = 0
        error = ''

        if not os.path.isdir(oldPath):
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if newName != oldName:
                if not os.path.exists(absolutePath):
                    error = translate(_(u'filemanager_error_file_not_found',
                                      default=u"File not found."),
                                      context=self.request)
                    code = 1

                elif os.path.exists(os.path.join(oldPath, newName)):
                    error = translate(_(u'filemanager_error_file_exists',
                                  default=u"File already exists."),
                                  context=self.request)
                    code = 1
                else:
                    os.rename(os.path.join(oldPath, oldName), 
                              os.path.join(oldPath, newName))

        return {
            "oldParent": self.normalizeReturnPath(os.path.split(oldPath)[-1]),
            "oldName": oldName,
            "newParent": self.normalizeReturnPath(os.path.split(oldPath)[-1]),
            "newName": newName,
            'error': error,
            'code': code,
        }

    def delete(self, path):
        """Delete the item at the given path.
        """

        path = path.encode('utf-8')

        absolutePath = self.getAbsolutePath(path)

        parentPath, name = os.path.split(absolutePath)

        code = 0
        error = ''

        if not os.path.isdir(parentPath):
            error = translate(_(u'filemanager_invalid_parent',
                              default=u"Parent folder not found."),
                              context=self.request)
            code = 1
        else:
            if not os.path.exists(absolutePath):
                error = translate(_(u'filemanager_error_file_not_found',
                                  default=u"File not found."),
                                  context=self.request)
                code = 1
            else:
                if not os.path.isdir(parentPath):
                    try:
                        os.remove(absolutePath)
                    except OSError, e:
                        if e.errno == 1:
                            error = translate(_(u'filemanager_error_not_allowed',
                                default=u"You are not allowed to remove this."),
                                context=self.request)
                            code = 1

                        elif e.errno == 13:
                            error = translate(_(u'filemanager_error_unauthorized',
                                      default=(u"You are not allowed to create a "
                                                "folder in \"%s\"." % path)),
                                      context=self.request)
                            code = 1
                        else:
                            error = translate(_(u'filemanager_error_unknown',
                                      default=(u"Something bad happened: "
                                                "\"%s\"." % e.strerror)),
                                      context=self.request)
                            code = 1
                else:
                    shutil.rmtree(absolutePath, ignore_errors=True)

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

        absolutePath = self.getAbsolutePath(path)
        name = self.getFilename(absolutePath)

        self.request.response.setHeader('Content-Type', 'application/octet-stream')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % name)

        return open(absolutePath, 'rb')

    # Helpers
    def getObject(self, path):
        raise NotImplementedError()

    def getAbsolutePath(self, key):
        """Given a key (i.e. a relative path), return an absolute path
        as utf-8, and make sure noone is trying to break out using "../".
        """

        if '..' in key:
            raise Unauthorized("Stay within your sandbox, please")

        if key and key.startswith('/'):
            key = key[1:]

        path = os.path.join(self.context.path, key)
        if isinstance(path, unicode):
            path = path.encode('utf-8')
        return path

    def getFilename(self, path):
        return path.split(os.path.sep)[-1]

    def getExtension(self, path):
        basename, ext = os.path.splitext(path)
        ext = ext[1:].lower()
        return ext

    # Methods that are their own views

    def getFile(self, path):
        self.setup()

        absolutePath = self.getAbsolutePath(path)
        ext = self.getExtension(absolutePath)

        result = {'ext': ext}

        if ext not in self.imageExtensions:
            openedFile = open(absolutePath, 'rb')
            result['contents'] = str(openedFile.read())
            openedFile.close()
        else:
            info = self.getInfo(path)
            result['info'] = self.previewTemplate(info=info)

        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    def saveFile(self, path, value):
        self.setup()

        path = self.getAbsolutePath(path)
        value = value.replace('\r\n', '\n').encode('utf-8')

        openedFile = open(path, 'wb')
        openedFile.write(value)
        openedFile.close()

        return ' '  # Zope no likey empty responses

    def filetree(self):
        self.setup()

        foldersOnly = bool(self.request.get('foldersOnly', False))

        def getFolder(rootPath, parentPath=''):
            result = []
            parent = os.path.join(rootPath, parentPath)
            for name in os.listdir(parent):
                key = os.path.join(parentPath, name)
                path = os.path.join(rootPath, key)
                if os.path.isdir(path):
                    item = {
                        'title': name,
                        'key': key,
                        'isFolder': True
                    }
                    item['children'] = getFolder(rootPath, key)
                    result.append(item)
                elif not foldersOnly and not self.getExtension(path) in self.ignoredExtensions:
                    item = {
                        'title': name,
                        'key': key,
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
