#!/usr/bin/env python3

import unittest
import subprocess
import shutil
import os
import os.path as path
import io

debug = False

# TODO:
#
# check that the integration refs saved in .git-subdir are always commit
# hashes not branch names
#
# check what happens if a .git-subdir is manually configured to have
# no external repo urls
#
# check what happens if the integration and upstream branches are the
# same? how is a rebase handled?
#
# what if the integration branch != last_integration_commit?
# should manual changes to the integration branch be ignored?
# 
# check initializing a non-toplevel subdir
# XXX: likely broken since most code refers to _subdir instead of a
# _subdir_path variable.
# XXX: we also don't consider the possibility of multiple subdirs
# with the same name in the same repo.
#
# test --pre-integrated-commit (expected broken a.t.m since we check
# subdir doesn't already exist as part of validate_new_subdir())
#
# check multiple edit, rebase cycles
#
# if we decided to keep the git subdir init cmd (arguably useful for
# --pre-integrated-commit option) then it could be good to test a
# manual add, in terms of 'init', 'fetch' + 'commit'
#
# test git subdir rebase --onto
#
# test git subdir push [--upstream]
#
# XXX: should git subdir push accept an arbitrary remote name?
#
# test cloning with a non-existent integration branch that the upstream
# is cloned (assuming the integration branch will later be initialized
# by pushing integrated/rebased changes)
#
# check that after a rebase git subdir status gives a warning that the
# last squashed commit has not yet been published


def shell(cmd):
    if debug:
        print(cmd)
    return subprocess.call(cmd, shell=True)


def shell_output(cmd):
    
    if debug:
        print(cmd)

    try:
        output = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except:
        output = ""

    if debug:
        print("# > " + "\n# > ".join(output.splitlines()))

    return output


class TestSubdir(unittest.TestCase):

    def make_repo(self, name):
        os.chdir(self.testdir)
        os.mkdir(name)
        os.chdir(name)
        shell('git init .')
        shell('touch empty')
        shell('git add empty')
        shell('git commit -m "empty"')
        shell('git config receive.denyCurrentBranch ignore')


    def commit(self, repo, filename, msg, contents):
        os.chdir(os.path.join(self.testdir, repo))

        with io.open(filename, 'w') as fp:
            fp.write(contents)

        shell('git add "' + filename + '"') 
        shell('git commit -m "' + msg + '" "' + filename + '"') 


    def commit_append(self, repo, filename, line):
        os.chdir(os.path.join(self.testdir, repo))

        with io.open(filename, 'a') as fp:
            fp.write(line + '\n')

        shell('git add "' + filename + '"') 
        shell('git commit -m "' + line + '" "' + filename + '"') 


    def commit_prepend(self, repo, filename, line):
        os.chdir(os.path.join(self.testdir, repo))

        with io.open(filename, 'r+t') as fp:
            content = fp.read()
            fp.seek(0)
            fp.write(line + '\n' + content)

        shell('git add "' + filename + '"') 
        shell('git commit -m "' + line + '" "' + filename + '"') 


    def file_contains(self, filename, line):
        with io.open(filename, 'r') as fp:
            content = fp.read()

        return line + '\n' in content


    def setUp(self):
        self.topdir = os.getcwd()
        self.testdir = os.path.join(os.getcwd(), 'test-area')
        if os.path.isdir("test-area"):
            shutil.rmtree("test-area")
        os.mkdir('test-area')
        os.chdir('test-area')
        self.make_repo('subdir_upstream')
        self.commit('subdir_upstream', 'sub-file.txt', 'initial',
                    'initial content\n')
        self.commit_append('subdir_upstream', 'sub-file.txt', 'sub line 1')
        self.commit_append('subdir_upstream', 'sub-file.txt', 'sub line 2')
        os.chdir(self.testdir)
        shell('git clone subdir_upstream subdir_integration')
        os.chdir('subdir_integration')
        shell('git config receive.denyCurrentBranch ignore')

        self.commit_prepend('subdir_upstream', 'sub-file.txt', 'upstream diverge 1')

        self.make_repo('container_repo')
        self.commit('container_repo', 'file.txt', 'initial',
                    'initial content\n')
        self.commit_append('container_repo', 'file.txt', 'line 1')

        self.commit('container_repo', 'other.txt', 'create other file',
                    'initial content\n')

        os.chdir(self.testdir)


    def tearDown(self):
        os.chdir(self.topdir)
        if path.isdir(self.testdir) and path.isdir(path.join(self.testdir, 'container_repo')):
            shutil.rmtree(self.testdir)


    def test_add_no_repo(self):
        """Cloning without specifying an integration repo is an error."""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add'), 2)
        self.assertEqual(shell('git subdir add ./foo'), 2)
        self.assertEqual(shell('git subdir add --upstream ../subdir_upstream --message "add subdir" ./foo'), 2)


    def test_add_with_integration_only(self):
        """Add with just integration repo."""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add ../subdir_integration --message "add subdir" ./foo'), 0)
        self.assertEqual(shell_output('git config -f foo/.git-subdir/config subdir.integration.url'), "../subdir_integration")
        self.assertEqual(shell_output('git config -f foo/.git-subdir/config subdir.upstream.url'), "")

        self.assertTrue(self.file_contains('foo/sub-file.txt', 'sub line 2'))


    def test_add_with_integration_and_upstream(self):
        """Add with integration and upstream repos."""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add ../subdir_integration --upstream ../subdir_upstream --message "add subdir" foo'), 0)
        self.assertEqual(shell_output('git config -f foo/.git-subdir/config subdir.integration.url'),
                         "../subdir_integration")
        self.assertEqual(shell_output('git config -f foo/.git-subdir/config subdir.upstream.url'),
                         "../subdir_upstream")

        self.assertTrue(self.file_contains('foo/sub-file.txt', 'sub line 2'))
        self.assertFalse(self.file_contains('foo/sub-file.txt', 'upstream diverge 1'))


    def test_add_repeat(self):
        """Attempting to add an existing subdir should fail."""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add --message "add subdir" ../subdir_integration ./subdir'), 0)
        self.assertEqual(shell('git subdir add --message "add subdir" ../subdir_integration ../subdir_upstream ./subdir'), 1)
        self.assertEqual(shell_output('git config -f subdir/.git-subdir/config subdir.integration.url'), "../subdir_integration")
        self.assertEqual(shell_output('git config -f subdir/.git-subdir/config subdir.upstream.url'), "")


    def test_branch(self):
        """Verify branch of unmodified subdir matches original upstream."""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir --debug add ../subdir_integration --message "add subdir" ./foo'), 0)
        self.assertEqual(shell('git subdir --debug branch -b test-branch ./foo'), 0)

        hash0 = shell_output('git rev-parse subdir-integration/foo/master')
        hash1 = shell_output('git rev-parse test-branch')
        self.assertEqual(hash0, hash1)


    def test_branch_local_change(self):
        """Verify branching of subdir with one local change."""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add ../subdir_integration --message "add subdir" ./foo'), 0)

        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 3')

        self.assertEqual(shell('git subdir branch -b test-branch ./foo'), 0)

        revs = shell_output('git rev-list --ancestry-path subdir-integration/foo/master..test-branch')
        revs = revs.splitlines()
        self.assertEqual(len(revs), 1)

        #self.assertEqual(shell('git show ' + revs[0] + ' | grep -q "local sub line 3"'), 0)
        self.assertEqual(shell_output('git diff-tree -s --pretty=%s ' + revs[0]),
                         'local sub line 3')

        self.assertFalse(path.exists('.git-subdir'))


    def test_branch_local_mixed_changes(self):
        """Verify branching of subdir with local subdir and other changes
        interleaved.
        """
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add ../subdir_integration --message "add subdir" ./foo'), 0)

        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 3')
        self.commit_append('container_repo', 'other.txt', 'other line 1')
        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 4')
        self.commit_append('container_repo', 'other.txt', 'other line 2')
        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 5')

        self.assertEqual(shell('git subdir branch -b test-branch ./foo'), 0)

        revs = shell_output('git rev-list --reverse --ancestry-path subdir-integration/foo/master..test-branch')
        revs = revs.splitlines()
        self.assertEqual(len(revs), 3)

        self.assertEqual(shell_output('git diff-tree -s --pretty=%s ' + revs[0]),
                         'local sub line 3')
        self.assertEqual(shell_output('git diff-tree -s --pretty=%s ' + revs[1]),
                         'local sub line 4')

        self.assertEqual(shell_output('git diff-tree -s --pretty=%s ' + revs[2]),
                         'local sub line 5')

        self.assertFalse(path.exists('.git-subdir'))


    # If only a single integration repo has been configured then it may be
    # treated as a hybrid upstream and integration repo with changes being
    # pushed to the repo that local changes should be rebased on but we can
    # also expect that the result of rebasing local changes will get pushed
    # back to this integration repo such that local changes aren't lost if we
    # squash commit this result to subdir.
    def test_rebase_with_integration_repo_only(self):
        """tests rebasing local subdir changes on upstream changes since
        last squash commit"""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add ../subdir_integration --message "add subdir" ./foo'), 0)

        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 3')
        self.commit_append('container_repo', 'other.txt', 'other line 1')
        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 4')
        self.commit_append('container_repo', 'other.txt', 'other line 2')
        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 5')

        self.commit_prepend('subdir_integration', 'sub-file.txt', 'integration update 1')
        self.commit_prepend('subdir_integration', 'sub-file.txt', 'integration update 2')

        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir rebase --message "rebase foo" ./foo'), 0)

        self.assertTrue(self.file_contains('foo/sub-file.txt', 'integration update 1'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'integration update 2'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'local sub line 3'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'local sub line 4'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'local sub line 5'))


    def test_rebase_with_integration_and_upstream(self):
        """tests rebasing local subdir changes on integration changes and
        rebasing those on the upstream changes since last squash commit"""
        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir add ../subdir_integration --upstream ../subdir_upstream --message "add subdir" ./foo'), 0)

        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 3')
        self.commit_append('container_repo', 'other.txt', 'other line 1')
        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 4')
        self.commit_append('container_repo', 'other.txt', 'other line 2')
        self.commit_append('container_repo', 'foo/sub-file.txt', 'local sub line 5')

        # xxx: how to also check rebasing on integration branch changes without
        # having a conflict with the upstream changes?

        self.commit_prepend('subdir_upstream', 'sub-file.txt', 'upstream update 1')
        self.commit_prepend('subdir_upstream', 'sub-file.txt', 'upstream update 2')

        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir rebase --message "rebase foo" ./foo'), 0)

        self.assertTrue(self.file_contains('foo/sub-file.txt', 'upstream diverge 1'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'upstream update 1'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'upstream update 2'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'local sub line 3'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'local sub line 4'))
        self.assertTrue(self.file_contains('foo/sub-file.txt', 'local sub line 5'))

        # Also test rebasing on changes made directly to the integration branch
        #self.commit_prepend('subdir_integration', 'sub-file.txt', 'integration update 1')
        #self.commit_prepend('subdir_integration', 'sub-file.txt', 'integration update 2')
        #self.commit_prepend('subdir_upstream', 'sub-file.txt', 'upstream update 3')

        #os.chdir(os.path.join(self.testdir, 'container_repo'))
        #self.assertEqual(shell('git subdir rebase --message "rebase foo" ./foo'), 0)

        #self.assertTrue(self.file_contains('foo/sub-file.txt', 'integration update 1'))
        #self.assertTrue(self.file_contains('foo/sub-file.txt', 'integration update 1'))
        #self.assertTrue(self.file_contains('foo/sub-file.txt', 'upstream update 3'))


    def test_push_integration(self):
        self.test_rebase_with_integration_and_upstream()

        os.chdir(os.path.join(self.testdir, 'container_repo'))
        self.assertEqual(shell('git subdir push ./foo'), 0)


if __name__ == "__main__":
    unittest.main()
