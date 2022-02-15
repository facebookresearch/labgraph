export const data = [
  [
    {
      NoiseGenerator: {
        type: "Node",
        config: {
          NoiseGeneratorConfig: {
            sample_rate: "float",
            num_features: "int",
          },
        },
        inputs: [],
        outputs: [
          {
            RandomMessage: {
              timestamp: "float",
              data: "np.ndarray",
            },
          },
        ],
      },
    },
    {
      RollingAverager: {
        type: "Node",
        state: {
          RollingState: {
            messages: "List.RandomMessage",
          },
        },
        config: {
          RollingConfig: {
            window: "float",
          },
        },
        inputs: [
          {
            RandomMessage: {
              timestamp: "float",
              data: "np.ndarray",
            },
          },
        ],
        outputs: [
          {
            RandomMessage: {
              timestamp: "float",
              data: "np.ndarray",
            },
          },
        ],
      },
    },
  ],
  [
    {
      RollingAverager: {
        type: "Node",
        state: {
          RollingState: {
            messages: "List.RandomMessage",
          },
        },
        config: {
          RollingConfig: {
            window: "float",
          },
        },
        inputs: [
          {
            RandomMessage: {
              timestamp: "float",
              data: "np.ndarray",
            },
          },
        ],
        outputs: [
          {
            RandomMessage: {
              timestamp: "float",
              data: "np.ndarray",
            },
          },
        ],
      },
    },
    {
      AveragedNoise: {
        type: "Group",
        config: {
          AveragedNoiseConfig: {
            sample_rate: "float",
            num_features: "int",
            window: "float",
          },
        },
        inputs: [],
        outputs: [
          {
            RandomMessage: {
              timestamp: "float",
              data: "np.ndarray",
            },
          },
        ],
        connections: {
          NoiseGenerator: "RollingAverager",
          RollingAverager: "AveragedNoise",
        },
      },
    },
  ],
  [
    {
      AveragedNoise: {
        type: "Group",
        config: {
          AveragedNoiseConfig: {
            sample_rate: "float",
            num_features: "int",
            window: "float",
          },
        },
        inputs: [],
        outputs: [
          {
            RandomMessage: {
              timestamp: "float",
              data: "np.ndarray",
            },
          },
        ],
        connections: {
          NoiseGenerator: "RollingAverager",
          RollingAverager: "AveragedNoise",
        },
      },
    },
    {
      Plot: {
        type: "Node",
        state: "PlotState",
        config: "PlotConfig",
        inputs: ["RandomMessage"],
        outputs: [],
      },
    },
  ],
];
