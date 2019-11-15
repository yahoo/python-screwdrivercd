# Github integration utilites

## SSH initialization

The `screwdrivercd_ssh_setup` utility initializes the ssh configuration sufficiently to start 
[ssh-agent](https://www.ssh.com/ssh/agent).

This utility does not have any settings.

## Deploykey setup

The `screwdrivercd_github_deploykey` setup utility will populate the github deploy key stored in
the `GIT_DEPLOY_KEY` secret into the [ssh-agent](https://www.ssh.com/ssh/agent)

This utility requires that [ssh-agent](https://www.ssh.com/ssh/agent) is already running.

### Secrets

| Secret         | Description                                  |
| -------------- | -------------------------------------------- |
| GIT_DEPLOY_KEY | Base64 encoded github deployment private key |

### Adding a deploy key to the CI Pipeline

Creating a new deploy key requires the [ssh-keygen](https://www.ssh.com/ssh/keygen/) and [base64](https://linux.die.net/man/1/base64)
command line utiliites.  These utilities are generally available as part of most Linux
and Mac OSX systems.

#### Step 1 - Create a new key

First create a new pem format key without a passphrase.  When prompted for a passphrase press enter.

!!! note "Command to create a new key called screwdrivercd_deploykey"

    ```console
    ssh-keygen -t rsa -b 4096 -C "dev-null@screwdriver.cd" -f screwdrivercd_deploykey
    ```

!!! example "Example: creating a key pem key with a filename of screwdrivercd_deploykey"

    ```console
    $ ssh-keygen -t rsa -b 4096 -C "dev-null@screwdriver.cd" -f screwdrivercd_deploykey
    Generating public/private rsa key pair.
    Enter passphrase (empty for no passphrase):
    Enter same passphrase again:
    Your identification has been saved in screwdrivercd_deploykey.
    Your public key has been saved in screwdrivercd_deploykey.pub.
    The key fingerprint is:
    SHA256:E49HJVZqvgeQ+4+VO9buDikq0XTPNSd+OI4OtXnLzdE dev-null@screwdriver.cd
    The key's randomart image is:
    +---[RSA 4096]----+
    |          o.o    |
    |         o +     |
    |        + +      |
    |        .X.   + .|
    |       oS.=o.o = |
    |      . .+ +o=+ o|
    |       .  = O+.+E|
    |      .  . B+=o+.|
    |       .. .o+=* o|
    +----[SHA256]-----+
    $
    ```

#### Step 2 - Convert the key to pem format

!!! note "Command to convert screwdrivercd_deploykey to pem format"

    ```console
    ssh-keygen -p -N ""  -m pem -f screwdrivercd_deploykey
    ```
    
!!! example "Example: Converting screwdrivercd_deploykey to pem format"

    ```console
    $ ssh-keygen -p -N ""  -m pem -f screwdrivercd_deploykey
    Key has comment 'dev-null@screwdriver.cd'
    Your identification has been saved with the new passphrase.
    $
    ```

#### Step 3 - Base64 encode the pem key and paste it in the screwdriver GIT_DEPLOY_KEY secret

!!! note "Command to get the base64 string of the screwdrivercd_deploykey to paste into the screwdriver pipeline GIT_DEPLOY_KEY secret"

    ```console
    base64 screwdrivercd_deploykey
    ```

!!! example "Example: getting the base64 encoded string to paste into the screwdriver pipeline GIT_DEPLOY_KEY secret"

    ```console hl_lines="2"
    $ base64 screwdrivercd_deploykey
    LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlKSndJQkFBS0NBZ0VBeDdKaEZMYVF6YXE4RkVKK29Ha2gySFg5NFhwODE4SzlERTlIM3h3WEVzM3FtQXFWClN6aTBtYUtzV3ljT21GTXhFU21SOFZPcHB3NUU0Z2l4eVNwOUFCVEh1SjFsQjQrWGRFb01KcDdqU1ozeDVaczQKRzNrRmZTbmtySGtPQW92UkhSRjdadU5zdTQxZ0JCTVdFSTlzQjBhUkRpNkJqaVQ2VHZzV2pnRDZtMmtESDZoMwprcFFwQ0ZFcGlTKzF4dDAxQkN3UHRjT3BSVG9xZlorVityTVgxa0dMajExT3FSd0crbnp6dS9lOEIrdmEzRnFUCmwxYVpFaUhZNDBCbVNhSnhKVUg0VlJYK2dGZGZlTS91dzRTQVA4NU9hR1ozZGNkU240L1d2cWlONURBSTRlWDAKUmR4VDJMOXZFM0lBUGtjeGhWNXRIKzd1djhmU0tnSUFsUStDbnlYc0c5NEVIeDk2RUJMM3FZZUdFSGo5RTFoWQpRbXRkenJWblFTaFplL05ROXJvN1FWRjE0YnI4ZVBQUGovSFQxdGRRSjc1VHYwRm91TGdYSnJlSFZIdXJieTJnCmpPOGxPZHI4eDNOYlExOEErRlllYnNtciswbm82aTRxOWNBcTI4bjJmYVM4a0haekxkM1hoR1Vzc04zMlBuQmEKTFdEaGRxYlVhL2VlODBvckxxcnJRVjd4M0dtZ2o0cnJhekgzUXVETXI2TVgvWmFoaFFsZ242cWJqR3R1c1FqNAorVmx2b2YxVXdsczFiQmQxdC9zdXQ5aXc0NlpQM0pyV3I3MkgrM1FRck9YNGMzWGRqYlpmN1BiWTFQcGZzQ3RvCkVKQlVJeWV5b29ySlU5K2NYV0xlNHRYYnJTd1I4S21TdkcxM2xPZzl1N0cwZWF3U0FuVjdoV2R5TXM4Q0F3RUEKQVFLQ0FnQTRUZFVOY0FRWDJPRzZuSnp6UVhFbmhPMFdHK0VEUEliczU1V09GRzkwLzlYN0ZGRFBxcWRSQWdxeQprS3FPekRYemJ0TVZSYzk1cUk1SFpNZ3J2ZTBNanM5WkFCZXlNQXcxMzRMWmlNYnd4TFdsVlVSV2lxSy9qWVpLCkVyK2VmQ2x6bHJCQ2JERUdHSEJQOWNtczFhTlIwZFdvTi9pVFNWM0IwdzJpOENlNGxiMHB1ZWdzemRWYjRQWmoKRmE2YzZWVy9YV1Q0akxnM0twVThZamg1UFBHbG1VbHVISkxISDMzZ05rYktZcWtEV3I2VWpuMDZtRklFU01MTQpJQ1kyOExRU0d5MlhYK0luOFhxYnA1VGNUNG1SYyt1cmgraDZycjVlK3NGRGRHYTlSY1hiVzJpcUlkc0tLNzkzCnJoYmZlRmRBRVVXWFVWakRmZVdGcnBiWGNFNFZiUEdBalZKbURnYlVmS21WQlVZSDJFNkpBYkJJTGRkYjZkQkgKcU5aT1hsbjdoVUxNeG9mdXI4NFVhaWQzVXBrdkZxdDdrYytOT0Y4VEgvNUpPajVzUzhYUGI4N0w5Z3MvWVlHZgpmRG9acHBpeUVVekp6R1d2d2xTd0p6eTNDa1dZSXdJQ1k5LytzNUVVczEvV2YwNllhbHQ5OE1XTkQvWE5rdThuCisvTGpYY3JlMjN0OHpZaHdUZHpZbzBwZXY2WjF1VEhtSC9BNXNPMHF6UnpxN3oyWkI1eWVEblpPUTFpT3J3WVMKdW1iVXBVRGxDbTIxa2RHc1o2Qjg5OWdON0NKMXhqdUJrbjRmNnRYeENNQUNHN0Y0dzl6YkxzOVRIMXYvZzVyagp1UjdDSVZMUnk1ajNZK1F4dmF1YzZoTThBYVpBOVpOQVUyalhLZE9keW42OWpUV2ZJUUtDQVFFQSs3bm9vL3JlClp5MHV2OC9STkdrUUlId20zcEVxOXFxSDYvRmJQb0g5Nkd4U0c5dzR5Z0sxVTllNzNVZlJQUmRiWjFvSWlvbFQKN21KdmswU3hTaThMV3hVS0hrclFTMEdvS0lxdG9Fck1neSszWU5nYnVsNlZCY1Z3YW50T0w0bm12cFZhMXdwQQo3czB3ekRtcHo0ejNMMWw2WmdrYTNVcmZjYSsrL2U4dzFobVRvVmNMRk5vMm9FemxJOW9kcE9PY0VPMlh2aFJKCkdYcXZNWC9CeTBiSGt5RHB0ZTk2ZlNyWVI3c2VFQ3RNZmRmZGU2SnVud2sxVWduay9uWjNtRjRBZW9ZYTgyblEKaWtQVnlpRTlWcHhWQjJIcGdLUGdPODBYcmVkSDU0SXNtZFBJMjJLMjRhaHVIeGFuSkt4VzBhTlR6MnlFN2Y1ZAp3KzF5Ny9iOHNLTk85d0tDQVFFQXl4WlZEQ3BLUmdTR25TTUFHamFCYUdjeEluTXhGYXFHSSswdzU3eUQ0VVVaCk9oM3grOG5pYzhTZFJuZkRxanBJbnl0RGdxbGdVemJreExXRGxESjd6Ynk2REN4Q29LRmFmYlBJeDJDRUppNjcKdzBiSHdJaXFneVJNMllsR05md3JHSHZNekNyT3QvS1NUUmw5MCt6czV2SCtUdEhIL0EycFBGWmZTdkdoNmY1UAp1SEY5UExFZ3dNM292c0Jka1A2aEl2SjRtWlkwcHl4OTNWQXI3T2Ftcm1LMEJqSXdnVmhudk1zK1g4eW10TWNHClFuQ3BHb1ZmNVZETEJlZGluckJRSkRqNGpYUGRPOUdpNGVVbHg1YWhMbGt6Tk5UWHRXR2dSczRORk1zajFla2YKVU9OMHJWcmY3Y3BtckVXYVJVT0dFT3JZaEsrUDFKanhNV01QdGhKTTZRS0NBUUJZc3lDVHI1Rnd2ODRLVHJ0RQpBWVZxUFBVaFZmdlNvVEoxNUQwbm9IeU15cWFBSkxCcUZsdzRwL3NOdFFHNHlpTXVIdDZGbW5CVnZwL2NQOGROCkFaaTV4b2NqTjIrQUpTbVE1NVRZdDZLcTAwU0Z2b0Mrd2hjMnltU2JVTW16SEorUEptZTFBR3J5K3FDb1JlVmQKT2luYnFHYmx6MjJFN3A0Zm5ETHJuYjRTb3o2UENuSGdMaWd6Z2dUNEJpS04rSm9FcVFQZ09adXNlN3VCOEtlago3bFBpdHlWRE01aHd4SWtqZFg3WmFiaHhXNEF5MFlDelQzWlhheDhpdnpIVEljUi9hQVBWSThNVkJXUXU3bG1ECnpHQjEwbjJLRTdTdXZjMExQVVRzQWNXZmlxM3JDRFN5L1R1WWZzMzBzVG1DYzAvVDlrUTg3SFd6MVZhNzBjY20Kb3RUdkFvSUJBRDIzVDZrZXdPdCtQSnBNSkovU3FJamRzeVRROUwyczBJN2lhZFpDaDZGUnFsVHEvTHFUbzJtaQorbGlMMUw1S2IvOU8ybmsrbDdNeUgxdFgvZUJ2WndnaXJqYzh6QktjZGk5MUR6TG50Y0VVdXFLaFE5clNyVjZsCkRXV2VQZVB4K2ZhNnlJWFRESGNDRkV1eHozY3pyTnFSOThKa0plNEhDTUw1VElRdDRoS0Y0aHdmQVB3TXAvTnYKbjZjNE5qYjE2bW9BWFgzdkU1a3FBQ1hkVXp2dTdBQmFwbktybGVuNHY2Mno1Z1NlNEpwWFVTT25zUHdLUkJZZgo4MUtiK25CWERFTzF2SExnSHY4cXVlRUVEZk1WWjIzNlZZRmNuU0RWeGlzK091Tnl5RFVkWHhMcHpHOVNDbkxzCjZ6NjIrQ2JNV2xXUnlMS3AxMyszNnJRamNvYldFT0VDZ2dFQVBJQ1FoYUt0STNUS0UrdFRzdFlvMVZZSDhwT04KSkZCZytSNFB6UnFXTWNHV0VSeVRmU0dDb1NzM0YyY0R5cHZXZG02bGRxRGNJVkw3MWxSdjF4d3IvRUFmeThhSwptY3haZ0VyYTZOSU14RFc3S2hjWUNiTjJBZ0RTc2dnMmtRbkR5NThHNmNiVW9ncGI3S0JtWVl4K0FjLzZ0Mnd0ClZkdGNXbTA3MXE4TE5qTms0Z0hRaHR6eE1VcmxkeDNhRGE0cXFYRHQveUFUbjlHSkx2THpTY3VTOHZYTnhDQXUKSkhVbTU0Z3RQR2pHWGpkb3pZUXE0cWI0T3oxcHJncXVFMGx6Mnd2bWRDWkE3RkZ3b2VGLzJ3MFFmSjBuZ1BkTwphSUtaaThYZElmM0FFc1pQcVhaYmcxdk1Nelh0b0pHVVpjVGJPVllVYzNyMXRqNHYvS01SR01BSHlBPT0KLS0tLS1FTkQgUlNBIFBSSVZBVEUgS0VZLS0tLS0K
    $
    ```
    
#### Step 4 - Get the contents of the new public key and paste it into a new github deploy_key

!!! note "Command to get the screwdrivercd_deploykey.pub key to paste into the github new deploy key window"
    
    ```console
    cat screwdrivercd_deploykey.pub
    ```

!!! example "Example: Get the screwdrivercd_deploykey.pub key to past into the github new deploy key window"
    
    ```console hl_lines="2"
    $ cat screwdrivercd_deploykey.pub
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDHsmEUtpDNqrwUQn6gaSHYdf3henzXwr0MT0ffHBcSzeqYCpVLOLSZoqxbJw6YUzERKZHxU6mnDkTiCLHJKn0AFMe4nWUHj5d0SgwmnuNJnfHlmzgbeQV9KeSseQ4Ci9EdEXtm42y7jWAEExYQj2wHRpEOLoGOJPpO+xaOAPqbaQMfqHeSlCkIUSmJL7XG3TUELA+1w6lFOip9n5X6sxfWQYuPXU6pHAb6fPO797wH69rcWpOXVpkSIdjjQGZJonElQfhVFf6AV194z+7DhIA/zk5oZnd1x1Kfj9a+qI3kMAjh5fRF3FPYv28TcgA+RzGFXm0f7u6/x9IqAgCVD4KfJewb3gQfH3oQEveph4YQeP0TWFhCa13OtWdBKFl781D2ujtBUXXhuvx488+P8dPW11AnvlO/QWi4uBcmt4dUe6tvLaCM7yU52vzHc1tDXwD4Vh5uyav7SejqLir1wCrbyfZ9pLyQdnMt3deEZSyw3fY+cFotYOF2ptRr957zSisuqutBXvHcaaCPiutrMfdC4Myvoxf9lqGFCWCfqpuMa26xCPj5WW+h/VTCWzVsF3W3+y632LDjpk/cmtavvYf7dBCs5fhzdd2Ntl/s9tjU+l+wK2gQkFQjJ7KiislT35xdYt7i1dutLBHwqZK8bXeU6D27sbR5rBICdXuFZ3Iyzw== dev-null@screwdriver.cd
    $
    ```
