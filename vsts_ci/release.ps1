echo $env:BUILD_SOURCEBRANCH
echo $env:RELEASE_PRIMARYARTIFACTSOURCEALIAS
echo $env:SYSTEM_DEFAULTWORKINGDIRECTORY/.pypirc
$artifact_name="build-artifact-drop"
$drop_file=Get-ChildItem -Path $env:SYSTEM_ARTIFACTSDIRECTORY/$env:RELEASE_PRIMARYARTIFACTSOURCEALIAS/$artifact_name/*.whl
$drop_file_name=$drop_file.Name
echo $drop_file_name
$tool_name=$drop_file_name.Split('-')[0]
echo $tool_name
$tool_version=$drop_file_name.Split('-')[1]
echo $tool_version
if ($env:BUILD_SOURCEBRANCH -match "^refs/tags/[\s\S]+$") {
    pip install twine
    echo "The current branch is tag"
    if ($env:BUILD_SOURCEBRANCH -match "^refs/tags/v?[0-9]+\.[0-9]+\.[0-9]+$") {
       echo "Uploading to production pypi"
       twine upload -r pypi "$env:SYSTEM_ARTIFACTSDIRECTORY/$env:RELEASE_PRIMARYARTIFACTSOURCEALIAS/$artifact_name/$drop_file_name" --config-file $env:SYSTEM_DEFAULTWORKINGDIRECTORY/.pypirc
       pip install --no-cache --upgrade "$tool_name==$tool_version"
    } else {
       echo "Uploading to test pypi"
       twine upload -r pypitest "$env:SYSTEM_ARTIFACTSDIRECTORY/$env:RELEASE_PRIMARYARTIFACTSOURCEALIAS/$artifact_name/$drop_file_name" --config-file $env:SYSTEM_DEFAULTWORKINGDIRECTORY/.pypirc
       pip install --no-cache --upgrade "$tool_name==$tool_version" --index-url "https://test.pypi.org/simple/" --extra-index-url "https://pypi.org/simple"
    }
} else {
    echo "The current branch is not a tag"
}