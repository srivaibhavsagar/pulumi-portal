yum install -y wget

wget https://s3.amazonaws.com/amazoncloudwatch-agent/assets/amazon-cloudwatch-agent.gpg -qP /tmp/cwagent

# Key value check
key_value=$(gpg --import /tmp/cwagent/amazon-cloudwatch-agent.gpg |& grep -Po '(3B789C72)')
if [ "$key_value" = "3B789C72" ]; then
    echo "Good key value, proceeding."
    # Public key fingerprint check
    key_fingerprint=$(gpg --fingerprint $key_value |& grep -Po '(9376 16F3 450B 7D80 6CBD  9725 D581 6730 3B78 9C72)')
    if [ "$key_fingerprint" = "9376 16F3 450B 7D80 6CBD  9725 D581 6730 3B78 9C72" ]; then
        echo "Good key fingerprint, proceeding."
        #Signature
        wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm.sig -qP /tmp/cwagent 1> /dev/null

        #Download package
        wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm -qP /tmp/cwagent 1> /dev/null
        # Package signature check
        verification_response=$(gpg --verify /tmp/cwagent/amazon-cloudwatch-agent.rpm.sig /tmp/cwagent/amazon-cloudwatch-agent.rpm |& grep -Po '(Good signature)')
        if [ "$verification_response" = "Good signature" ]; then
            echo "Good signature, proceeding."
        else 
            echo "BAD signature, can't proceed."
        fi
    else 
        echo "BAD key fingerprint, can't proceed."
    fi
else 
    echo "BAD key value, can't proceed."
fi


# Unpack package
rpm -U /tmp/cwagent/amazon-cloudwatch-agent.rpm

yum remove -y wget

touch /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Add your custom .json here, this one is to push RAM usage of the server to CW.
cat <<EOF > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
{
	"agent": {
		"metrics_collection_interval": 60,
		"run_as_user": "root"
	},
	"logs": {
		"logs_collected": {
			"files": {
				"collect_list": [
					{
						"file_path": "",
						"log_group_name": ".",
						"log_stream_name": "{instance_id}",
						"retention_in_days": -1
					},
					{
						"file_path": "",
						"log_group_name": ".",
						"log_stream_name": "{instance_id}",
						"retention_in_days": -1
					}
				]
			}
		}
	},
	"metrics": {
		"aggregation_dimensions": [
			[
				"InstanceId"
			]
		],
		"append_dimensions": {
			"AutoScalingGroupName": "${aws:AutoScalingGroupName}",
			"ImageId": "${aws:ImageId}",
			"InstanceId": "${aws:InstanceId}",
			"InstanceType": "${aws:InstanceType}"
		},
		"metrics_collected": {
			"collectd": {
				"metrics_aggregation_interval": 60
			},
			"cpu": {
				"measurement": [
					"cpu_usage_idle",
					"cpu_usage_iowait",
					"cpu_usage_user",
					"cpu_usage_system"
				],
				"metrics_collection_interval": 60,
				"resources": [
					"*"
				],
				"totalcpu": false
			},
			"disk": {
				"measurement": [
					"used_percent",
					"inodes_free"
				],
				"metrics_collection_interval": 60,
				"resources": [
					"*"
				]
			},
			"diskio": {
				"measurement": [
					"io_time",
					"write_bytes",
					"read_bytes",
					"writes",
					"reads"
				],
				"metrics_collection_interval": 60,
				"resources": [
					"*"
				]
			},
			"mem": {
				"measurement": [
					"mem_used_percent"
				],
				"metrics_collection_interval": 60
			},
			"netstat": {
				"measurement": [
					"tcp_established",
					"tcp_time_wait"
				],
				"metrics_collection_interval": 60
			},
			"statsd": {
				"metrics_aggregation_interval": 60,
				"metrics_collection_interval": 60,
				"service_address": ":8125"
			},
			"swap": {
				"measurement": [
					"swap_used_percent"
				],
				"metrics_collection_interval": 60
			}
		}
	}
}
EOF

sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
