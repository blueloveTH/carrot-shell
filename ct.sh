# create a loop
while true; do
    # check env variable 'CTSH_EXIT
    if [ -n "$CTSH_EXIT" ]; then
        # delete env variable 'CTSH_EXIT'
        unset CTSH_EXIT
        break
    fi
    # check env variable 'CTSH_CONDA_ENV'
    if [ -z "$CTSH_CONDA_ENV" ]; then
        conda activate $CTSH_CONDA_ENV
        # delete env variable 'CTSH_CONDA_ENV'
        unset CTSH_CONDA_ENV
    fi
    python -m ctsh
done