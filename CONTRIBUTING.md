# Contributing

To make contributions to this charm, you'll need a working [development setup](https://juju.is/docs/sdk/dev-setup).

You can use the environments created by `tox` for development:

```shell
tox --notest -e unit
source .tox/unit/bin/activate
```

## Testing

This project uses `tox` for managing test environments. There are some pre-configured environments
that can be used for linting and formatting code when you're preparing contributions to the charm:

```shell
tox -e fmt           # update your code according to linting rules
tox -e lint          # code style
tox -e unit          # unit tests
tox                  # runs 'lint', 'unit', 'static' and 'code-coverage' environments
```

### Integration tests

To run the integration tests locally, you'll need to build the flask image first and load it into docker.  
the following assume that you are running microk8s locally with the registry plugin.

```shell
cd sample_rock/
rockcraft pack
rockfile="$(find . -name "*.rock" -printf "%f")"
IFS=_ read -r image_name version _ <<< "$(echo "$rockfile")"
/snap/rockcraft/current/bin/skopeo --insecure-policy copy "oci-archive:$rockfile" "docker-daemon:$image_name:$version"
docker tag $image_name:$version localhost:32000/$image_name:$version
docker push localhost:32000/$image_name:$version
```

Then you can run the integration tests.

```shell
tox -e integration -- --flask-app-image localhost:32000/$image_name:$version
```


## Build the charm

Build the charm in this git repository using:

```shell
charmcraft pack
```

<!-- You may want to include any contribution/style guidelines in this document>
