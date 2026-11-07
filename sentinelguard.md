# SentinelGuard: my final year project

## The big picture
My final year project (FYP) is a smart industrial control system: a zero trust framework for IoT devices, with a focus on reliability. I prefer not to share more detail about the wider project. We are a group of 4 people. The part I'm working on is called SentinelGuard.

## What SentinelGuard is
SentinelGuard is an IoT-based automated safety and liquid control system. It monitors the fluid level in physical tanks and automates pump and valve operations in real time.

## How it's built
The system is built around an ESP32 microcontroller, relay modules and ultrasonic sensors. The ultrasonic sensors measure how full a tank is, the ESP32 decides what to do, and the relay modules switch the pumps and valves on and off.

Data moves over the MQTT protocol, which is lightweight and works well for IoT devices. The system uses custom setpoints, so the operator can choose the levels at which pumps and valves act. It also has fail-safe rules, so that overflows and system failures are prevented even when something goes wrong.

Everything is controlled through a custom operator console interface.

## Why reliability matters
The goal is a system that is reliable, because a tank that overflows or a pump that fails has real physical consequences. That is why SentinelGuard is built with fail-safe rules and automated safety checks instead of relying on manual control.

## Where SentinelGuard fits
SentinelGuard is the project's hardware and control side, and it sits inside the larger FYP goal of a zero trust framework for IoT devices.
