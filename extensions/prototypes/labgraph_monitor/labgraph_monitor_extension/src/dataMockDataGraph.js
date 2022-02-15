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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
        },
      },
    },
    {
      Node2: {
        type: "Group",
        config: {
          Node2Config: {
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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
        },
      },
    },
    {
      Node4: {
        type: "Group",
        config: {
          Node2Config: {
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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
        },
      },
    },
    {
      Node5: {
        type: "Group",
        config: {
          Node2Config: {
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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
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
  [
    {
      Node2: {
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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
        },
      },
    },
    {
      Node6: {
        type: "Group",
        config: {
          Node2Config: {
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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
        },
      },
    },
    {
      Node7: {
        type: "Group",
        config: {
          Node2Config: {
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
          RollingAverager: "Node2",
          RollingAverager: "Node4",
          RollingAverager: "Node5",
          Node2: "Node6",
          Node2: "Node7",
        },
      },
    },
  ],
];
