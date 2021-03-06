Travis CI: [![Build Status](https://travis-ci.org/rib/git-subdir.svg?branch=master)](https://travis-ci.org/rib/git-subdir)

Integrate the content of a repository into a subdirectory
>     git subdir add [-b <branch>] [--upstream-branch <branch>] <repository> [<upstream-repo>] <subdir>
>     git subdir fetch [<subdir>…]
>     git subdir commit[-m <message] [--dry-run] <commit> [<subdir>]
>     git subdir branch [-b branch] [<subdir>]
>     git subdir update [<subdir>]
>     git subdir push [--upstream] [--dry-run] [<subdir>]
>     git subdir status [<subdir>…]
>     git subdir config --key <key> [--value <value>] [--unset] [<subdir>]

DESCRIPTION
===========

*git subdir* maintains the content of an external Git repository within a subdirectory of your repository.

Local changes to the subdirectory can be filtered onto a branch and pushed back upstream. Long lived integration changes (such as to integrate an external project into your build system) are maintained on a branch and rebased each time you update to the latest upstream.

Developers can clone your project and freely commit changes to subdirectories without needing to know about or use *git subdir* which can be considered a project maintainer’s tool; only needed when re-syncing a subdirectory’s content with upstream.

COMMANDS
========

add
---

>     git subdir add [-b <branch>] [--upstream-branch <branch>] [-m <msg>]
>                     [--pre-integrated-commit CORRESPONDING_COMMIT]
>                     <repository> [<upstream-repository] <subdir>

Creates a &lt;subdir&gt;/ directory containing a .git-subdir/config file with a record of the corresponsing remote &lt;repository&gt; as well as (optionally) an upstream repository to monitor.

The &lt;repository&gt; would typically be a project-specific fork of an upstream repository and is referred to as the *integration* repository.

The benefit of specifying a second, upstream repository is that *git subdir update* can streamline rebasing any project-specific &lt;subdir&gt; changes onto the latest upstream changes.

Typically &lt;subdir&gt; wouldn’t exist before running *git subdir add*, but it’s also possible to create a .git-subdir/config file for a pre-existing subdirectory (in which case --pre-integrated-commit must be passed to identify a commit from &lt;repository&gt; that the subdirectory’s content currently corresponds to).

The initial &lt;subdir&gt; content will come from the &lt;repository&gt; branch if it already exists otherwise it will come from the &lt;upstream-repository&gt;.

### options

-q; --quiet  
Pass --quiet to *git subdir fetch* to silence other internally used git commands. Progress is not reported to the standard error stream.

-v; --verbose  
Be verbose.

-b; --branch  
The branch to fetch and maintain integration changes on. By default this is *master*

--upstream-branch  
If an &lt;upstream-repository&gt; has been specified then it’s also possible to specify which upstream branch to monitor. By default this is *master*

fetch
-----

>     git subdir fetch [<subdir>]

Fetches branches and tags from the configured *upstream* and *integration* repositories

### options

-q; --quiet  
Pass --quiet to *git subdir fetch* to silence other internally used git commands. Progress is not reported to the standard error stream.

-v; --verbose  
Be verbose.

commit
------

>     git subdir commit [-m <msg>] [--dry-run] <commit> [<subdir>]

Replaces the contents of &lt;subdir&gt; with the contents of &lt;commit&gt; in a single squashed commit. &lt;commit&gt; should be in the layout of the external repository.

If the &lt;commit&gt; is not an upstream commit it should then be pushed to the remote integration branch for others to be able to rebase your project-specific changes onto different upstream versions. Running *git subdir status* will try to warn when the last squashed &lt;commit&gt; doesn’t appear to have been published for others. (See *git subdir push*)

Note: it’s ok to rebase these squash commits on a topic branch without confusing *git subdir*, but it’s recommended to avoid squashing extra changes into these commits, because commands like *git subdir branch* you will split these extra changes back out into a separate, poorly named patch.

Note: Every time new content is squash committed to a subdirectory then *git subdir* also creates a *ref* for the commit whose content was used so that it can be referenced as a base for later *git subdir* commands. These refs need to be published to your remote integration repo for other project maintainers too. (See *git subdir push*)

Note: the extra squash commit references effectively connect the revision history of the subdirectory with that of the external project, but this connection is only preserved within the integration branch so users fetching your project don’t also end up fetching the full history of these external projects. When the squash commit is first made then the reference is stored in &lt;subdir&gt;/.git-subdir/refs and when pushed to your remote integration repo these are stored under .git/refs/git-subdir/.

branch
------

>     git subdir branch -b <branch> [<subdir>]

Creates a branch in the layout of the external project, and filters any patches that affect &lt;subdir&gt; onto this branch too. The branch is based on an upstream commit so it’s possible to manually push changes upstream from here. Another use case might be to manually rebase on a more recent upstream before committing the result with *git subdir commit*.

update
------

>     git subdir update [<subdir>]

This fetches from the configured upstream and integration repositories, then (if both branches have been configured) rebases integration changes on the latest upstream changes, rebases any local changes on top of this and then commits the result.

This is the recommended way to routinely pull in new upstream changes to &lt;subdir&gt;.

This is a convenience for the following steps:

1.  Running *git subdir fetch*

2.  Running *git subdir branch* to filter local &lt;subdir&gt; changes onto a branch based on your last subdirectory squash commit

3.  Running *git rebase* to rebase that branch on the latest upstream or integration branch

4.  Running *git subdir commit* to squash the result back into your current branch

status
------

>     git subdir status [<subdir>…]

Prints out the configuration for each &lt;subdir&gt;, including warnings about commits that have been integrated with *git subdir commit* but have not yet been published for others.

config
------

>     git subdir config --key <key> [--value <value>] [<subdir>]
>     git subdir config --key <key> [--unset] [<subdir>]

>     examples:
>       git subdir config --key upstream.url <subdir>
>       git subdir config --key upstream.url --value https://foo.git <subdir>
>       git subdir config --key upstream.branch --value foo <subdir>
>       git subdir config --key upstream.branch --unset <subdir>
>       git subdir config --key integration.url <subdir>

Note: this deviates from the standard *git config* &lt;option&gt; \[&lt;value&gt;\] UI due to the ambiguity of &lt;value&gt; and &lt;subdir&gt; both being optional

EXAMPLE
=======

Lets say you have a container project *super* at <https://github.com/user/super> and another project *duper* at <https://github.com/upstream/duper> which you want to embed in the former.

The first thing to decide is where to maintain an *integration* branch for any changes you might need to track for the *duper* subdirectory.

Lets assume you don’t have privileges to touch the *upstream/duper* repo so you start by forking it and create <https://github.com/user/duper>. We’ll leave the master branch of this repo alone and create a *super-integration* branch that we can push to <https://github.com/user/duper>.

    $ cd super/
    $ git subdir add -b super-integration http://github.com/user/duper http://github.com/upstream/duper duper/

Now make a local change to the duper/ subdirectory…

    $ echo "foo" > duper/file.txt
    $ git commit -m 'change file' duper/file.txt

At this point the upstream may have improvements we want, while we still want to keep our change.

    $ git subdir update duper

Will fetch the latest upstream, rebase the local change and commit the result back.

If you run *git subdir status duper* now you will see a warning.

As part of this update your local change was rebased on upstream and *git subdir status* is reminding you to push the rebased branch as your latest super-integration branch.

Every time new contents are squash committed to a subdirectory (either via a *git subdir commit* or a *git subdir update*) then *git subdir* also creates a *ref* for the commit whose content was used so that the commit can always be used as a base for later *git subdir* commands. In addition to the integration branch, these refs should be published for other project maintainers too. Note that these references effectively connect the revision history of the subdirectory with that of the external project, but this connection is only preserved within the integration branch so users fetching your project don’t also end up fetching the full history of these external projects.

*git subdir push* will push your integration branch (super-integration) and commit refs to your configured integration repo:

    $ git subdir push duper

CONFIGURATION
=============

*git subdir* maintains the configuration for a subdirectory in a .git-subdir/config file which is tracked as part of your repository history. These files are compatible with *git config -f .git-subdir/config* and it’s safe to modify (and commit) changes to .git-subdir/config files with the exception that the *commit-uuid* line should not be touched since that will interfere with *git subdir* identifying the changes that update the subdir contents.

*git subdir* will create *subdir-upstream/&lt;subdir&gt;* and *subdir-integration/&lt;subdir&gt;* remotes in $GIT\_DIR/ but never assumes these exist and always updates them before use based on the current .git-subdir configuration.

COMPARED TO SIMILAR TOOLS
=========================

*git subdir* serves a similar purpose to git-submodule(1), git-subtree(1) so here are a few notes to help distinguish the tools.

*git submodule*  
-   Developers cloning a repo that uses *git subdir* don’t need to know about or use *git subdir*.

-   *git subdir* incorporates external content via squash commits that themselves don’t retain any history of the external project whereas *git submodule* works as an assistant for cloning external git repositories within subdirectories of your project.

*git subtree*  
-   *git subtree* isn’t designed to facilitate rebasing integration changes for an external repository and is generally geared around using merge commits to sync with upstream. For long lived integration changes, this may mean dealing with with conflicts without the original context of the changes when merging.

-   Similarly *git subtree* doesn’t have provisions for rebasing local, upstreamable changes.

LICENSE
=======

The MIT License
