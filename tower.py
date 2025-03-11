Temp_Wiping_Gcode = """
;Tower_Layer_Gcode
G92 E0
G1 X20 Y10.19
G1 F9600
G1 X20 Y20 E.25658
G1 X29.81 Y20 E.25658
G1 E-.21 F5400
;WIPE_START
G1 F9600
G1 X28.81 Y20 E-.09
;WIPE_END
G1 X23.71 Y25.679 F30000
G1 X20 Y29.81
G1 E.3 F5400
G1 F9600
G1 X20 Y20 E.25658
G1 X10.19 Y20 E.25658
G1 E-.21 F5400
;WIPE_START
G1 F9600
G1 X11.19 Y20 E-.09
;WIPE_END
G1 X17.943 Y23.556 F30000
G1 X29.8 Y29.8
G1 E.3 F5400
G1 F9547.071
G1 X10.2 Y29.8 E.61454
G1 X10.2 Y10.2 E.61454
G1 X29.8 Y10.2 E.61454
G1 X29.8 Y29.76 E.61329
G92 E0
G1 E-.21 F5400
;WIPE_START
G1 F9547.071
G1 X28.8 Y29.762 E-.09
;WIPE_END
G1 X28.7 Y29.76
;Tower_Layer_Gcode Finished
""" 
Temp_Tower_Base_Layer_Gcode = """
;Tower_Base_Layer_Gcode
G1 X19.681 Y20.319
EXTRUDER_REFILL
G1 F9600
G1 X19.681 Y20.319 E.02318
G1 X20.319 Y20.319 E.02318
G1 X20.319 Y19.681 E.02318
G1 X19.681 Y19.681 E.02318
G1 X19.304 Y19.304 F30000
G1 F9600
G1 X20.696 Y19.304 E.05059
G1 X20.696 Y20.696 E.05059
G1 X19.304 Y20.696 E.05059
G1 X19.304 Y19.304 E.05059
G1 X18.927 Y18.927 F30000
G1 F9600
G1 X21.073 Y18.927 E.078
G1 X21.073 Y21.073 E.078
G1 X18.927 Y21.073 E.078
G1 X18.927 Y18.927 E.078
G1 X18.55 Y18.55 F30000
G1 F9600
G1 X18.55 Y21.45 E.1054
G1 X21.45 Y21.45 E.1054
G1 X21.45 Y18.55 E.1054
G1 X18.55 Y18.55 E.1054
G1 X18.173 Y18.173 F30000
G1 F9600
G1 X18.173 Y21.827 E.13281
G1 X21.827 Y21.827 E.13281
G1 X21.827 Y18.173 E.13281
G1 X18.173 Y18.173 E.13281
G1 X17.796 Y17.796 F30000
G1 F9600
G1 X22.204 Y17.796 E.16022
G1 X22.204 Y22.204 E.16022
G1 X17.796 Y22.204 E.16022
G1 X17.796 Y17.796 E.16022
G1 X17.419 Y17.419 F30000
G1 F9600
G1 X22.581 Y17.419 E.18763
G1 X22.581 Y22.581 E.18763
G1 X17.419 Y22.581 E.18763
G1 X17.419 Y17.419 E.18763
G1 X17.042 Y17.042 F30000
G1 F9600
G1 X22.958 Y17.042 E.21504
G1 X22.958 Y22.958 E.21504
G1 X17.042 Y22.958 E.21504
G1 X17.042 Y17.042 E.21504
G1 X16.664 Y16.664 F30000
G1 F9600
G1 X16.664 Y23.336 E.24245
G1 X23.336 Y23.336 E.24245
G1 X23.336 Y16.664 E.24245
G1 X16.664 Y16.664 E.24245
G1 X16.287 Y16.287 F30000
G1 F9600
G1 X16.287 Y23.713 E.26986
G1 X23.713 Y23.713 E.26986
G1 X23.713 Y16.287 E.26986
G1 X16.287 Y16.287 E.26986
G1 X15.91 Y15.91 F30000
G1 F9600
G1 X24.09 Y15.91 E.29726
G1 X24.09 Y24.09 E.29726
G1 X15.91 Y24.09 E.29726
G1 X15.91 Y15.91 E.29726
G1 X15.533 Y15.533 F30000
G1 F9600
G1 X15.533 Y24.467 E.32467
G1 X24.467 Y24.467 E.32467
G1 X24.467 Y15.533 E.32467
G1 X15.533 Y15.533 E.32467
G1 X15.156 Y15.156 F30000
G1 F9600
G1 X15.156 Y24.844 E.35208
G1 X24.844 Y24.844 E.35208
G1 X24.844 Y15.156 E.35208
G1 X15.156 Y15.156 E.35208
G1 X14.779 Y14.779 F30000
G1 F9600
G1 X25.221 Y14.779 E.37949
G1 X25.221 Y25.221 E.37949
G1 X14.779 Y25.221 E.37949
G1 X14.779 Y14.779 E.37949
G1 X14.402 Y14.402 F30000
G1 F9600
G1 X14.402 Y25.598 E.4069
G1 X25.598 Y25.598 E.4069
G1 X25.598 Y14.402 E.4069
G1 X14.402 Y14.402 E.4069
G1 X14.025 Y14.025 F30000
G1 F9600
G1 X14.025 Y25.975 E.43431
G1 X25.975 Y25.975 E.43431
G1 X25.975 Y14.025 E.43431
G1 X14.025 Y14.025 E.43431
G1 X13.648 Y13.648 F30000
G1 F9600
G1 X26.352 Y13.648 E.46172
G1 X26.352 Y26.352 E.46172
G1 X13.648 Y26.352 E.46172
G1 X13.648 Y13.648 E.46172
G1 X13.271 Y13.271 F30000
G1 F9600
G1 X13.271 Y26.729 E.48913
G1 X26.729 Y26.729 E.48913
G1 X26.729 Y13.271 E.48913
G1 X13.271 Y13.271 E.48913
G1 X12.894 Y12.894 F30000
G1 F9600
G1 X12.894 Y27.106 E.51653
G1 X27.106 Y27.106 E.51653
G1 X27.106 Y12.894 E.51653
G1 X12.894 Y12.894 E.51653
G1 X12.517 Y12.517 F30000
G1 F9600
G1 X12.517 Y27.483 E.54394
G1 X27.483 Y27.483 E.54394
G1 X27.483 Y12.517 E.54394
G1 X12.517 Y12.517 E.54394
G1 X12.14 Y12.14 F30000
G1 F9600
G1 X12.14 Y27.86 E.57135
G1 X27.86 Y27.86 E.57135
G1 X27.86 Y12.14 E.57135
G1 X12.14 Y12.14 E.57135
G1 X11.762 Y11.762 F30000
G1 F9600
G1 X28.238 Y11.762 E.59876
G1 X28.238 Y28.238 E.59876
G1 X11.762 Y28.238 E.59876
G1 X11.762 Y11.762 E.59876
G1 X11.385 Y11.385 F30000
G1 F9600
G1 X28.615 Y11.385 E.62617
G1 X28.615 Y28.615 E.62617
G1 X11.385 Y28.615 E.62617
G1 X11.385 Y11.385 E.62617
G1 X11.008 Y11.008 F30000
G1 F9600
G1 X28.992 Y11.008 E.65358
G1 X28.992 Y28.992 E.65358
G1 X11.008 Y28.992 E.65358
G1 X11.008 Y11.008 E.65358
G1 X10.631 Y10.631 F30000
G1 F9600
G1 X29.369 Y10.631 E.68099
G1 X29.369 Y29.369 E.68099
G1 X10.631 Y29.369 E.68099
G1 X10.631 Y10.631 E.68099
G1 X10.254 Y10.254 F30000
G1 F9600
G1 X29.746 Y10.254 E.70839
G1 X29.746 Y29.746 E.70839
G1 X10.254 Y29.746 E.70839
G1 X10.254 Y10.254 E.70839
G1 X9.877 Y9.877 F30000
G1 F9600
G1 X30.123 Y9.877 E.7358
G1 X30.123 Y30.123 E.7358
G1 X9.877 Y30.123 E.7358
G1 X9.877 Y9.877 E.7358
G1 X9.5 Y9.5 F30000
G1 F9600
G1 X9.5 Y30.5 E.76321
G1 X30.5 Y30.5 E.76321
G1 X30.5 Y9.5 E.76321
G1 X9.5 Y9.5 E.76321
G1 X9.123 Y9.123 F30000
G1 F9600
G1 X9.123 Y30.877 E.79062
G1 X30.877 Y30.877 E.79062
G1 X30.877 Y9.123 E.79062
G1 X9.123 Y9.123 E.79062
G1 X8.746 Y8.746 F30000
G1 F9600
G1 X31.254 Y8.746 E.81803
G1 X31.254 Y31.254 E.81803
G1 X8.746 Y31.254 E.81803
G1 X8.746 Y8.746 E.81803
G1 X8.369 Y8.369 F30000
G1 F9600
G1 X8.369 Y31.631 E.84544
G1 X31.631 Y31.631 E.84544
G1 X31.631 Y8.369 E.84544
G1 X8.369 Y8.369 E.84544
G1 X7.992 Y7.992 F30000
G1 F9600
G1 X32.008 Y7.992 E.87285
G1 X32.008 Y32.008 E.87285
G1 X7.992 Y32.008 E.87285
G1 X7.992 Y7.992 E.87285
G1 X7.615 Y7.615 F30000
G1 F9600
G1 X7.615 Y32.385 E.90025
G1 X32.385 Y32.385 E.90025
G1 X32.385 Y7.615 E.90025
G1 X7.615 Y7.615 E.90025
G1 X7.238 Y7.238 F30000
G1 F9600
G1 X32.762 Y7.238 E.92766
G1 X32.762 Y32.762 E.92766
G1 X7.238 Y32.762 E.92766
G1 X7.238 Y7.238 E.92766
G1 X6.86 Y6.86 F30000
G1 F9600
G1 X33.14 Y6.86 E.95507
G1 X33.14 Y33.14 E.95507
G1 X6.86 Y33.14 E.95507
G1 X6.86 Y6.86 E.95507
G1 X6.86 Y5.9
EXTRUDER_RETRACT
;Tower Base Layer Finished
"""