# Exercises/Daily Workout

## Description

The subagent involves the creation of a workout for the currently active weekday, determining phase and length for each.

## Future Features

* Allow the user to create workouts for future phase components as well.

## Example Output

```
----------------------------------------
| No | True Flag       | Exercise                     | Phase Component            | Bodypart    | Warmup | Duration                             | WDuration                            | BStrain | Sec/Exer | Reps | Sets    | Rest | 1RM | Weight | Intensity | Volume | Density | Performance |
| 1  | False Exercise  | hamstrings mfr               | flexibility-stabilization  | total body  | True   | 01 minutes, 30 seconds               | 01 minutes, 30 seconds               | 2       | 30 sec   | 1    | 3       | 0    |     |        |           | 3      | 1.0     | 3.0         |
| 2  | True Exercise   | standing cable row           | resistance-stabilization   | back        | False  | 11 minutes, 30 seconds               | 07 minutes                           | 3       | 7 sec    | 20   | 3       | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |
| 3  | True Exercise   | seated dumbbell biceps curl  | resistance-stabilization   | biceps      | False  | 11 minutes, 30 seconds               | 07 minutes                           | 2       | 7 sec    | 20   | 3       | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |

----------------------------------------

| Warm-Up |
| Sub | Set | No | True Flag       | Exercise                     | Phase Component            | Bodypart    | Warmup | Duration                             | WDuration                            | BStrain | Sec/Exer | Reps | Rest | 1RM | Weight | Intensity | Volume | Density | Performance |
| -   | 1   | 1  | False Exercise  | Hamstrings MFR               | flexibility-stabilization  | total body  | True   | 30 seconds                           | 30 seconds                           | 2       | 30 sec   | 1    | 0    |     |        |           | 3      | 1.0     | 3.0         |
| -   | 2   | 1  | False Exercise  | Hamstrings MFR               | flexibility-stabilization  | total body  | True   | 30 seconds                           | 30 seconds                           | 2       | 30 sec   | 1    | 0    |     |        |           | 3      | 1.0     | 3.0         |
| -   | 3   | 1  | False Exercise  | Hamstrings MFR               | flexibility-stabilization  | total body  | True   | 30 seconds                           | 30 seconds                           | 2       | 30 sec   | 1    | 0    |     |        |           | 3      | 1.0     | 3.0         |

| Vertical Set 1 |
| Sub | Set | No | True Flag       | Exercise                     | Phase Component            | Bodypart    | Warmup | Duration                             | WDuration                            | BStrain | Sec/Exer | Reps | Rest | 1RM | Weight | Intensity | Volume | Density | Performance |
| 1   | 1   | 2  | True Exercise   | standing cable row           | resistance-stabilization   | back        | False  | 03 minutes, 50 seconds               | 02 minutes, 20 seconds               | 3       | 7 sec    | 20   | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |
| 2   | 1   | 3  | True Exercise   | seated dumbbell biceps curl  | resistance-stabilization   | biceps      | False  | 03 minutes, 50 seconds               | 02 minutes, 20 seconds               | 2       | 7 sec    | 20   | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |

| Vertical Set 2 |
| Sub | Set | No | True Flag       | Exercise                     | Phase Component            | Bodypart    | Warmup | Duration                             | WDuration                            | BStrain | Sec/Exer | Reps | Rest | 1RM | Weight | Intensity | Volume | Density | Performance |
| 1   | 2   | 2  | True Exercise   | standing cable row           | resistance-stabilization   | back        | False  | 03 minutes, 50 seconds               | 02 minutes, 20 seconds               | 3       | 7 sec    | 20   | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |
| 2   | 2   | 3  | True Exercise   | seated dumbbell biceps curl  | resistance-stabilization   | biceps      | False  | 03 minutes, 50 seconds               | 02 minutes, 20 seconds               | 2       | 7 sec    | 20   | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |

| Vertical Set 3 |
| Sub | Set | No | True Flag       | Exercise                     | Phase Component            | Bodypart    | Warmup | Duration                             | WDuration                            | BStrain | Sec/Exer | Reps | Rest | 1RM | Weight | Intensity | Volume | Density | Performance |
| 1   | 3   | 2  | True Exercise   | standing cable row           | resistance-stabilization   | back        | False  | 03 minutes, 50 seconds               | 02 minutes, 20 seconds               | 3       | 7 sec    | 20   | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |
| 2   | 3   | 3  | True Exercise   | seated dumbbell biceps curl  | resistance-stabilization   | biceps      | False  | 03 minutes, 50 seconds               | 02 minutes, 20 seconds               | 2       | 7 sec    | 20   | 90   | 8   | 5      | 50        | 300    | 0.6     | 180.0       |

```