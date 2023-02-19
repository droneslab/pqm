
import numpy as np
COMPELTENESS_STR = 'completeness'
ARTIFACTS_STR = 'artifacts'
RESOLUTION_STR = 'resolution'
ACCURACY_STR = 'accuracy'
QUALITY_STR = 'quality'
METRICS_STR = 'metrics'

CHAMFER_STR = 'chamfer'
NORMALIZED_CHAMFER_STR = 'normalized_chamfer'
HOUSDORFF_STR = 'hausdorff'

METRICS_LIST = [COMPELTENESS_STR, ARTIFACTS_STR, RESOLUTION_STR, ACCURACY_STR, QUALITY_STR]

EPSILON_STR = 'e'
WEIGHT_COMPLETENESS_STR = 'wc'
WEIGHT_ARTIFACTS_STR = 'wt'
WEIGHT_RESOLUTION_STR = 'wr'
WEIGHT_ACCURACY_STR = 'wa'

OPTIONS_LIST = [EPSILON_STR, WEIGHT_COMPLETENESS_STR, WEIGHT_ARTIFACTS_STR, WEIGHT_RESOLUTION_STR, WEIGHT_ACCURACY_STR]

AVERAGE_STR = 'average'
VARIANCE_STR = 'variance'
TOTAL_STR = 'total'

CELL_DIM_STR = 'cell_dim'
MIN_BOUND_STR = 'min_bound'
MAX_BOUND_STR = 'max_bound'
CELL_SIZE_STR = 'cell_size'


CONFIG_GT_FILE_STR = 'gt_file'
CONFIG_CND_FILE_STR = 'cnd_file'
CONFIG_CELL_SIZE_STR = 'cell_size'
CONFIG_OPTIONS_STR = 'options'
CONFIG_SAVE_PATH_STR = 'save_path'

CONFIG_WEIGHTS_STR = 'weights'
CONFIG_EPS_STR = 'eps'

GT_COLOR = np.array([0.0, 1.0, 0.0])
CND_COLOR = np.array([0.0, 0.0, 1.0])
GREEN_COLOR = np.array([0.0, 1.0, 0.0])
RED_COLOR = np.array([1.0, 0.0, 0.0])

DENSITY_GT_STR = 'density_gt'
DENSITY_CND_STR = 'density_cnd'

CONFIG_DAMAGE_STR = 'damage'
CONFIG_DAMAGE_PARAMS_STR = 'damage_params'