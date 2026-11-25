"""Sensors. ROS-backed ones live in ``ros_sensors``; import them from there."""

from .observations import OdometryObservation, RGBObservation

__all__ = ['OdometryObservation', 'RGBObservation']
