#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2025, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

#Overwright history
#Author: Kotaro Kajitsuka
#Changed to use AprilTag from ArUco Marker and eye-on-base calibratoin from eye-in-hand calibration.

from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
def launch_setup(context, *args, **kwargs):
    robot_ip = LaunchConfiguration('robot_ip')
    robot_type = LaunchConfiguration('robot_type')
    dof = LaunchConfiguration('dof', default=7)
    hw_ns = LaunchConfiguration('hw_ns', default='')

    #marker_size = LaunchConfiguration('marker_size', default=0.0615)
    #marker_id = LaunchConfiguration('marker_id', default=6)
    marker_size = LaunchConfiguration('marker_size', default=0.09265)
    marker_id = LaunchConfiguration('marker_id', default=3)
    #marker_size = LaunchConfiguration('marker_size', default=0.0309)
    #marker_id = LaunchConfiguration('marker_id', default=190)
    

    camera_serial = LaunchConfiguration('camera_serial', default='')
    device_type = LaunchConfiguration('device_type', default='')
    usb_port_id = LaunchConfiguration('usb_port_id', default='')
    robot_type = robot_type.perform(context)
    dof = dof.perform(context)
    hw_ns = hw_ns.perform(context)
    marker_size = float(marker_size.perform(context))
    marker_id = int(marker_id.perform(context))
    camera_serial = str(camera_serial.perform(context))
    device_type = str(device_type.perform(context))
    usb_port_id = str(usb_port_id.perform(context))
    if hw_ns == '':
        hw_ns = 'xarm' if robot_type == 'xarm' else 'ufactory'
    if robot_type == 'lite' or robot_type == 'uf850':
        dof = '6'
    calib_filename = '{}_rs_on_base_calibration'.format(robot_type)
    rs_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('realsense2_camera'), 'launch', 'rs_launch.py'])),
        launch_arguments={
            'serial_no': camera_serial,
            'device_type': device_type,
            'usb_port_id': usb_port_id,
            'publish_tf': 'false',
            # 'camera_name': 'D435i',
            # 'camera_namespace': 'camera',
        }.items(),
    )
    raw_view = Node(
        package= 'image_view',
        executable='image_view',
        name='color_raw_view',
        remappings= [('/image', '/camera/camera/color/image_raw')]
    )

    apriltag_detector = Node(
        package='apriltag_ros',
        executable='apriltag_node',
        parameters=[{
            'image_transport': 'raw',
            'family': '36h11',
            'size': marker_size,
            'max_hamming': 0,
            'pose_estimation_method': 'pnp',
            'tag.ids': [marker_id],
            'tag.frames': ['camera_marker'],
            'tag.sizes': [marker_size],
            'detector.threads': 2,
            'detector.decimate': 2.0,
            'detector.blur': 0.0,
            'detector.refine': True,
            'detector.sharpening': 0.25,
            'detector.debug': False,
        }],
        remappings=[
            ('/image_rect', '/camera/camera/color/image_raw'),
            ('/camera_info', '/camera/camera/color/camera_info'),
        ],
    )
    robot_moveit_fake_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('xarm_moveit_config'), 'launch', '_robot_moveit_realmove.launch.py'])),
        launch_arguments={
            'dof': dof,
            'robot_ip': robot_ip,
            'robot_type': robot_type,
            'hw_ns': hw_ns,
            'no_gui_ctrl': 'false',
            # 'show_rviz': 'false',
            # 'add_realsense_d435i': 'true',
             'add_d435i_links': 'true',
        }.items(),
    )
    easy_handeye_calib_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('easy_handeye2'), 'launch', 'calibrate.launch.py'])),
        launch_arguments={
            'name': calib_filename,
            'calibration_type': 'eye_on_base',
            'tracking_base_frame': 'camera_color_optical_frame',
            'tracking_marker_frame': 'camera_marker',
            'robot_base_frame': 'link_base',
            'robot_effector_frame': 'link_eef',
            # 'move_group_namespace': '/',
            # 'move_group': '{}{}'.format(robot_type, dof if robot_type != 'uf850' else ''),
            'freehand_robot_movement': 'true',
            'automatic_robot_movement': 'true'
        }.items(),
    )
    recognition_view = Node(
        package='image_view',
        executable='image_view',
        remappings=[('/image', '/tag_detections_image')],
        ### arguments=['--ros-args --remap image:=/tag_detections_image']
    )
    return [
        rs_camera_launch,
        raw_view,
        apriltag_detector,
        robot_moveit_fake_launch,
        easy_handeye_calib_launch,
        recognition_view  #何も出ないので、オフに
    ]
def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])