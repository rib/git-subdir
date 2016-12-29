# Copyright (C) 2006,2007 Shawn O. Pearce <spearce@spearce.org>
# Copyright (C) 2016 Robert Bragg <robert@sixbynine.org>
#
# Based on some code from bash/zsh completion support for core Git.
#
# Distributed under the GNU General Public License, version 2.0.
#
# Note: this depends on implementation details of the completion
# support for core Git
#

__git_subdir_count_positionals()
{
    local word i c=0

    # Skip "git" (first argument)
    for ((i=1; i < ${#words[@]}; i++)); do
        word="${words[i]}"

        case "$word" in
            -*)
                continue
                ;;
            "subdir")
                # Skip the specified git command and discard git
                # main options
                ((c = 0))
                ;;
            "$1")
                # Skip the specified git subdir command and discard git or
                # subdir main options
                ((c = 0))
                ;;
            ?*)
                ((c++))
                ;;
        esac
    done

    printf "%d" $c
}

__git_subdir_find_subdirs()
{
    local subdirs=''
    local subdir=''

    for subdir in $(echo ./*/.git-subdir)
    do
        if test -f $subdir; then
            subdirs="$(dirname $subdir) $subdirs"
        fi
    done

    echo -n $subdirs
}

_git_subdir()
{
    local subcommands='init fetch commit clone branch rebase push status config'
    local subcommand=$(__git_find_on_cmdline "$subcommands")
    local n_positionals=$(__git_subdir_count_positionals "$subcommand")
    local init_opts="--branch --upstream= --upstream-branch= --pre-integrated-commit= "
    local clone_opts="--branch --upstream= --upstream-branch= --message "
    local fetch_opts="--progress"
    local branch_opts="--branch= "
    local rebase_opts="--local --onto= "
    local push_opts="--upstream --dry-run "
    local commit_opts="--message= --dry-run "
    local config_opts="--key= --value= --unset "

    case "$subcommand,$cur" in
        ,--*)
            __gitcomp '--debug'
            return
            ;;
        ,*)
            __gitcomp "init fetch commit clone branch rebase push status config"
            ;;
        init,--*)
            __gitcomp "$init_opts"
            return
            ;;
        init,*)
            if test $n_positionals -eq 0; then
                init_opts="$init_opts <repository> [<upstream>] <subdir> "
            fi
            if test $n_positionals -lt 3; then
                init_opts="$init_opts [<upstream>] <subdir> "
            fi
            __gitcomp "$init_opts "
            return
            ;;
        fetch,--*)
            __gitcomp "$fetch_opts "
            return
            ;;
        fetch,*)
            __gitcomp "$fetch_opts $(__git_subdir_find_subdirs)"
            return
            ;;
        commit,--*)
            __gitcomp "$commit_opts "
            return
            ;;
        commit,*)
            if test $n_positionals -eq 0; then
                commit_opts="$commit_opts $(__git_subdir_find_subdirs)"
            fi
            __gitcomp "$commit_opts"
            return
            ;;
        clone,--*)
            __gitcomp "$clone_opts"
            return
            ;;
        clone,*)
            if test $n_positionals -eq 0; then
                clone_opts="$clone_opts <repository> [<upstream>] <subdir> "
            fi
            if test $n_positionals -lt 3; then
                clone_opts="$clone_opts [<upstream>] <subdir> "
            fi
            __gitcomp "$clone_opts "
            return
            ;;
        branch,--*)
            __gitcomp "$branch_opts"
            return
            ;;
        branch,*)
            if test $n_positionals -eq 0; then
                branch_opts="$branch_opts $(__git_subdir_find_subdirs)"
            fi
            __gitcomp "$branch_opts"
            return
            ;;
        rebase,--*)
            __gitcomp "$rebase_opts"
            return
            ;;
        rebase,*)
            if test $n_positionals -eq 0; then
                rebase_opts="$rebase_opts $(__git_subdir_find_subdirs)"
            fi
            __gitcomp "$rebase_opts"
            return
            ;;
        push,--*)
            __gitcomp "$push_opts"
            return
            ;;
        push,*)
            if test $n_positionals -eq 0; then
                push_opts="$push_opts $(__git_subdir_find_subdirs)"
            fi
            __gitcomp "$push_opts"
            return
            ;;
        status,*)
            __gitcomp "$(__git_subdir_find_subdirs)"
            return
            ;;
        config,--key=*)
            __gitcomp "upstream.url upstream.branch integration.url integration.branch" "" "${cur#*=}"
            return
            ;;
        config,--*)
            __gitcomp "$config_opts"
            return
            ;;
        config,*)
            if test $n_positionals -eq 0; then
                config_opts="$config_opts $(__git_subdir_find_subdirs)"
            fi
            __gitcomp "$config_opts"
            return
            ;;
    esac
}
