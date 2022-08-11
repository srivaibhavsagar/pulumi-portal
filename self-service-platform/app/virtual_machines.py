from flask import (Blueprint, current_app, request, flash,
                   redirect, url_for, render_template)

import pulumi
import pulumi_aws as aws
import pulumi.automation as auto
import os
from pathlib import Path
from  .vars import *

bp = Blueprint("virtual_machines", __name__, url_prefix="/vms")
instance_types = ['t1.micro','t2.micro', 'c5.xlarge', 'p2.xlarge', 'p3.2xlarge']


def create_pulumi_program(keydata: str, instance_type=str, stack_name=str,project_name=str):
    # Choose the latest minimal amzn2 Linux AMI.
    # TODO: Make this something the user can choose

    server = aws.ec2.Instance(stack_name,
                              instance_type=instance_type,
                              
                              tags= { 
                                "Name": stack_name,
                              },ami="ami-0e34bbddc66def5ac")

    pulumi.export('instance_type', server.instance_type)
    pulumi.export('id', server.id)
    pulumi.export('privateIP', server.private_ip)
    pulumi.export('privateDNS', server.private_dns)
    pulumi.export('project',project_name)



@bp.route("/new", methods=["GET", "POST"])
def create_vm():
    """creates new VM"""
    if request.method == "POST":
        stack_name = request.form.get("vm-id")
        keydata = request.form.get("vm-keypair")
        instance_type = request.form.get("instance_type")

        def pulumi_program():
            return create_pulumi_program(keydata, instance_type, stack_name,project_name)
        try:
            # project_name='testing'
            project_settings=auto.ProjectSettings(
            name=project_name,
            runtime="python",
            backend={"url": "s3://my-bucket-8ff2384"})

            secrets_provider = "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2"
            # kms_env = os.environ.get("KMS_KEY")
            # kms_env = "cf305f60-1fac-414b-b0f5-6b975d66725a"

            if kms_env:
                secrets_provider = f"awskms://{kms_env}?region={curr_region}"
            if secrets_provider == "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2":
                raise Exception("Please provide an actual KMS key for secrets_provider")

            stack_settings=auto.StackSettings(
                secrets_provider=secrets_provider)

            # create or select a stack matching the specified name and project.
            # this will set up a workspace with everything necessary to run our inline program (pulumi_program)
            stack = auto.create_or_select_stack(stack_name=str(stack_name),
                                                project_name=project_name,
                                                program=pulumi_program,
                                                opts=auto.LocalWorkspaceOptions(project_settings=project_settings,
                                                                                secrets_provider=secrets_provider,
                                                                                stack_settings={str(stack_name): stack_settings}))

            print("successfully initialized stack")
            # for inline programs, we must manage plugins ourselves
            print("installing plugins...")
            stack.workspace.install_plugin("aws", "v4.0.0")
            print("plugins installed")

            stack.set_config("aws:region", auto.ConfigValue(curr_region))

            # deploy the stack, tailing the logs to stdout
            stack.up(on_output=print)
            flash(
                f"Successfully created VM '{stack_name}'", category="success")
        except auto.StackAlreadyExistsError:
            flash(
                f"Error: VM with name '{stack_name}' already exists, pick a unique name",
                category="danger",
            )
        return redirect(url_for("virtual_machines.list_vms"))

    current_app.logger.info(f"Instance types: {instance_types}")
    return render_template("virtual_machines/create.html", instance_types=instance_types, curr_instance_type=None)


@bp.route("/", methods=["GET"])
def list_vms():
    """lists all vms"""
    vms = []
    # org_name = current_app.config["PULUMI_ORG"]
    # project_name = 'testing'
    for project_name in projects:
            
        print (project_name)
        try:
            ws = auto.LocalWorkspace(
                project_settings=auto.ProjectSettings(
                    name=project_name, runtime="python",
                backend={"url": "s3://my-bucket-8ff2384"})
            )
            secrets_provider = "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2"
                # kms_env = os.environ.get("KMS_KEY")
            # kms_env = "cf305f60-1fac-414b-b0f5-6b975d66725a"

            if kms_env:
                secrets_provider = f"awskms://{kms_env}?region={curr_region}"
            if secrets_provider == "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2":
                raise Exception("Please provide an actual KMS key for secrets_provider")

            stack_settings=auto.StackSettings(
                    secrets_provider=secrets_provider)
            project_settings=auto.ProjectSettings(
                name=project_name,
                runtime="python",
                backend={"url": "s3://my-bucket-8ff2384"})

            all_stacks = ws.list_stacks()
            for stack in all_stacks:
                stack = auto.select_stack(
                    stack_name=stack.name,
                    project_name=project_name,
                    # no-op program, just to get outputs
                    program=lambda: None,opts=auto.LocalWorkspaceOptions(project_settings=project_settings,
                                                    secrets_provider=secrets_provider,
                                                    stack_settings={str(stack.name): stack_settings})
                )

                outs = stack.outputs()
                #print (outs)
                if 'privateIP' in outs:
                    vms.append(
                        {
                            "name": stack.name,
                            "id": f"{outs['id'].value}",
                            "dns_name": f"{outs['privateIP'].value}",
                            # "console_url": f"https://app.pulumi.com/{org_name}/{project_name}/{stack.name}",
                            # "project":f"{outs['project'].value}",
                        }
                    )
                
        except Exception as exn:
            flash(str(exn), category="danger")

        current_app.logger.info(f"VMS: {vms}")
        return render_template("virtual_machines/index.html", vms=vms)




@bp.route("/<string:id>/update", methods=["GET", "POST"])
def update_vm(id: str):
    stack_name = id
    if request.method == "POST":
        current_app.logger.info(
            f"Updating VM: {stack_name}, form data: {request.form}")
        keydata = request.form.get("vm-keypair")
        current_app.logger.info(f"updating keydata: {keydata}")
        instance_type = request.form.get("instance_type")

        def pulumi_program():
            return create_pulumi_program(keydata, instance_type, stack_name)
        try:
            project_name='testing'
            project_settings=auto.ProjectSettings(
            name=project_name,
            runtime="python",
            backend={"url": "s3://my-bucket-8ff2384"})

            secrets_provider = "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2"
            # kms_env = os.environ.get("KMS_KEY")
            kms_env = "cf305f60-1fac-414b-b0f5-6b975d66725a"

            if kms_env:
                secrets_provider = f"awskms://{kms_env}?region=eu-west-2"
            if secrets_provider == "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2":
                raise Exception("Please provide an actual KMS key for secrets_provider")

            stack_settings=auto.StackSettings(
                secrets_provider=secrets_provider)

            # create or select a stack matching the specified name and project.
            # this will set up a workspace with everything necessary to run our inline program (pulumi_program)
            stack = auto.select_stack(stack_name=str(stack_name),
                                                project_name=project_name,
                                                program=pulumi_program,
                                                opts=auto.LocalWorkspaceOptions(project_settings=project_settings,
                                                                                secrets_provider=secrets_provider,
                                                                                stack_settings={str(stack_name): stack_settings}))

            print("successfully initialized stack")
            # for inline programs, we must manage plugins ourselves
            print("installing plugins...")
            stack.workspace.install_plugin("aws", "v4.0.0")
            print("plugins installed")
   
            # stack = auto.select_stack(
            #     stack_name=stack_name,
            #     project_name=current_app.config["PROJECT_NAME"],
            #     program=pulumi_program
            # )
            
            stack.set_config("aws:region", auto.ConfigValue("eu-west-2"))
            # deploy the stack, tailing the logs to stdout
            stack.up(on_output=print)
            flash(f"VM '{stack_name}' successfully updated!",
                  category="success")
        except auto.ConcurrentUpdateError:
            flash(
                f"Error: VM '{stack_name}' already has an update in progress",
                category="danger",
            )
        except Exception as exn:
            flash(str(exn), category="danger")
        return redirect(url_for("virtual_machines.list_vms"))
    project_name='testing'
    project_settings=auto.ProjectSettings(
            name=project_name,
            runtime="python",
            backend={"url": "s3://my-bucket-8ff2384"})

    secrets_provider = "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2"
            # kms_env = os.environ.get("KMS_KEY")
    kms_env = "cf305f60-1fac-414b-b0f5-6b975d66725a"

    if kms_env:
        secrets_provider = f"awskms://{kms_env}?region=eu-west-2"
    if secrets_provider == "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2":
        raise Exception("Please provide an actual KMS key for secrets_provider")

    stack_settings=auto.StackSettings(
                secrets_provider=secrets_provider)
    stack = auto.select_stack(
        stack_name=stack_name,
        project_name=project_name,
        # noop just to get the outputs
        program=lambda: None,opts=auto.LocalWorkspaceOptions(project_settings=project_settings,
                                                                                secrets_provider=secrets_provider,
                                                                                stack_settings={str(stack_name): stack_settings})
    )
    outs = stack.outputs()
    public_key = outs.get("public_key")
    pk = public_key.value if public_key else None
    instance_type = outs.get("instance_type")
    return render_template("virtual_machines/update.html", name=stack_name, public_key=pk, instance_types=instance_types, curr_instance_type=instance_type.value)


@bp.route("/<string:id>/delete", methods=["POST"])
def delete_vm(id: str):
    stack_name = id
    try:
        secrets_provider = "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2"
            # kms_env = os.environ.get("KMS_KEY")
        kms_env = "cf305f60-1fac-414b-b0f5-6b975d66725a"

        if kms_env:
            secrets_provider = f"awskms://{kms_env}?region=eu-west-2"
        if secrets_provider == "awskms://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee?region=us-west-2":
            raise Exception("Please provide an actual KMS key for secrets_provider")
        project_name='testing'
        stack_settings=auto.StackSettings(
                secrets_provider=secrets_provider)
        project_settings=auto.ProjectSettings(
            name=project_name,
            runtime="python",
            backend={"url": "s3://my-bucket-8ff2384"})

        stack = auto.select_stack(
            stack_name=stack_name,
            project_name=project_name,
            # noop program for destroy
            program=lambda: None,opts=auto.LocalWorkspaceOptions(project_settings=project_settings,
                                                secrets_provider=secrets_provider,
                                                stack_settings={str(stack_name): stack_settings})
        )
        stack.destroy(on_output=print)
        stack.workspace.remove_stack(stack_name)
        flash(f"VM '{stack_name}' successfully deleted!", category="success")
    except auto.ConcurrentUpdateError:
        flash(
            f"Error: VM '{stack_name}' already has update in progress",
            category="danger",
        )
    except Exception as exn:
        flash(str(exn), category="danger")

    return redirect(url_for("virtual_machines.list_vms"))
