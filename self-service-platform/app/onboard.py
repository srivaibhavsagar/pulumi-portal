from flask import (Blueprint, current_app, request, flash,
                   redirect, url_for, render_template)

import pulumi
import pulumi_aws as aws
import pulumi.automation as auto
import os
from pathlib import Path
from pulumi import ResourceOptions
from  .vars import *

bp = Blueprint("onboard", __name__, url_prefix="/onboard")
# instance_types = ['t1.micro','t2.micro', 'c5.xlarge', 'p2.xlarge', 'p3.2xlarge']
# project_name='testing'
# kms_env = "cf305f60-1fac-414b-b0f5-6b975d66725a"
# curr_region='eu-west-2'


def create_pulumi_program(instance_type=str, stack_name=str,instance_det=str):
    # Choose the latest minimal amzn2 Linux AMI.
    # TODO: Make this something the user can choose

    server = aws.ec2.Instance(stack_name,
                              instance_type=instance_type,
                              
                              tags= { 
                                "Name": stack_name,
                              },ami="ami-0e34bbddc66def5ac",
    opts=ResourceOptions(import_=instance_det))

    pulumi.export('instance_type', server.instance_type)
    pulumi.export('id', server.id)
    pulumi.export('privateIP', server.private_ip)
    pulumi.export('privateDNS', server.private_dns)


@bp.route("/vm", methods=["GET", "POST"])
def onboard_vm():
    """creates new VM"""
    if request.method == "POST":
        stack_name = request.form.get("vm-id")
        instance_det = request.form.get("instance-id")
        # keydata = request.form.get("vm-keypair")
        instance_type = request.form.get("instance_type")

        def pulumi_program():
            return create_pulumi_program(instance_type, stack_name,instance_det)
        try:
            project_name='IOD'
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
                f"Successfully onboarded a VM '{stack_name}'", category="success")
        except auto.StackAlreadyExistsError:
            flash(
                f"Error: VM with name '{stack_name}' already exists, pick a unique name",
                category="danger",
            )
        return redirect(url_for("virtual_machines.list_vms"))

    current_app.logger.info(f"Instance types: {instance_types}")
    return render_template("onboard/create.html", instance_types=instance_types, curr_instance_type=None)


