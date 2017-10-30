"""
Author: Ivan Larinin

Example:
    import houdini_localizer
    houdini_localizer.HoudiniLocalizer().selected_nodes()

"""


import hou
import os
import shutil
import re
import time


class HoudiniLocalizer(object):
    """
    Collects all external paths to project_env directory

    Works on selected nodes, iterate through all of them and grab external paths
    check if external paths are valid and moves files to env_directory

    If files already in the env_directory but don't have relative paths changes it to relative
    Skips if relative paths

    """

    ext_to_subfolder = dict(
        textures='textures',
        geo="geo",
        other='misc',
        pictures='pictures'
        # ...
    )
    ext_to_type = dict(
        textures=['.bmp', '.jpg', '.jpeg', '.tif', '.gif', '.tiff', '.rgb', '.png', '.exr', '.pic', '.rat', '.hdr'],
        geo=['.geo', '.bgeo', '.obj', '.vdb', '.gz', 'sc', '.abc', '.fbx']
        # ...
    )
    collect_folder = 'collect'

    def __init__(self, project_env=None):
        # variables
        self.project_env = project_env or '$HIP'
        self.project_root = hou.expandString(self.project_env)
        self.errors = []

    def selected_nodes(self):
        """
        Selected nodes
        """
        sel = hou.selectedNodes()
        if sel:
            print '\n selected nodes are %s \n' % ([i.name() for i in sel])
            return self.new_path(sel)
        else:
            self.errors = ['Selection is empty!']
            self.display_error()

    @staticmethod
    def get_string_parms(node):
        """
        List of nodes parms
        """
        parms = []
        if not node.isInsideLockedHDA():
            for parm in node.parms():
                try:
                    parm.expression()
                except hou.OperationFailed:
                    if isinstance(parm.parmTemplate(), hou.StringParmTemplate):
                        if parm.parmTemplate().stringType() == hou.stringParmType.FileReference:
                            if parm.eval() != "":
                                parms.append(parm)
        return parms

    def new_path(self, sel):
        """
        Set new path
        """
        nodes = []
        for x in sel:
            nodes += x.allSubChildren()
            nodes.append(x)
        for node in nodes:
            parms = self.get_string_parms(node)
            if parms:
                for parm in parms:
                    path = parm.unexpandedString()
                    if not path.startswith(self.project_env):
                        parm.set(self.new_name(path, node))
        if self.errors:
            self.errors.insert(0, '! Following paths are wrong !')
            self.display_error()

    def display_error(self):
        if hou.isUIAvailable():
            self.errors = "\n".join(self.errors)
            hou.ui.displayMessage(str(self.errors), severity=hou.severityType.Warning)

    def new_name(self, path, node):
        """
        Create new relative path
        """
        # variables
        node_category = node.type().category().name()
        full_path = hou.expandString(path)
        base_name = os.path.basename(path)
        ext = os.path.splitext(path)[-1]

        base_path = self.project_env + '/' + self.collect_folder + '/'

        if not os.path.exists(full_path) and '$F' not in base_name:
            error = 'ERROR, path not exists %s (%s) node path %s' % (path, full_path, node.path())
            self.errors.append(error)
            return

        if not full_path.startswith(self.project_root):
            # new path init
            if ext in self.ext_to_type['textures']:
                new_path = base_path + self.ext_to_subfolder['textures'] + '/' + node.name() + '/' + base_name
                if node_category == 'Shop' or node_category == 'Vop':
                    new_path = base_path + self.ext_to_subfolder['pictures'] + '/' + node.name() + '/' + base_name
                    # create subfolders

            elif ext in self.ext_to_type['geo']:
                new_path = base_path + self.ext_to_subfolder['geo'] + '/' + node.name() + '/' + base_name

            else:
                new_path = base_path + self.ext_to_subfolder['other'] + '/' + node.name() + '/' + base_name

            # copy files to project
            self.copy_file_to_project(path, new_path, base_name)
        else:
            new_path = full_path.replace(self.project_root, self.project_env)

        return new_path

    def copy_file_to_project(self, src, dist, base_name):
        """
        Copy files to collect folders
        """
        dist_exp = os.path.normpath(os.path.dirname(hou.expandString(dist)))

        print '\n moving -- %s -- to the new directory -- %s' % (src, dist)

        if '$F' not in src:
            src = hou.expandString(src)
            self.check_file(src, dist_exp)
        elif '$F' in src:
            pat = re.sub('\$F\d*', '\\d+', os.path.basename(src))
            src_dir = hou.expandString(os.path.dirname(src))
            f_print = ''

            for file in os.listdir(src_dir):
                if re.match(pat, file):
                    src = os.path.normpath(os.path.join(src_dir, file))
                    self.check_file(src, dist_exp)
                    f_print = 'moved'
                else:
                    f_print = 'no matches were found'
            print '%s -- in -- %s -- for -- %s' % (f_print, src_dir, base_name)

    def check_file(self, src, dist):
        """
        Check folders
        Check files creation time
        """
        file_path = os.path.join(dist, os.path.basename(src))

        if not os.path.exists(dist):
            os.makedirs(dist)

        if not os.path.exists(file_path):
            try:
                shutil.move(src, dist)
            except WindowsError:
                error = 'Access is denied. !!pass!! %s' % src
                self.errors.append(error)
        else:
            t_src = time.ctime(os.path.getctime(src))
            t_dist = time.ctime(os.path.getctime(dist))
            if t_src > t_dist:
                try:
                    shutil.move(src, dist)
                    error = 'file already exists in the destination folder. !! Overwritten !! ' \
                          'Creation time source : %s \n Creation time destination : %s' % (t_src, t_dist)
                    self.errors.append(error)
                except WindowsError:
                    error = 'Access is denied. !!pass!! %s' % src
                    self.errors.append(error)

            else:
                error = 'file already exists in the destination folder. !! Not Moved !! ' \
                      'Creation time source : %s \n Creation time destination : %s' % (t_src, t_dist)
                self.errors.append(error)
