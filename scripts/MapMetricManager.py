

from QualityMetric import  calculate_complete_quality_metric
import numpy as np
import open3d as o3d

import copy
import json

from util import get_cropping_bound, get_cropped_point_cloud, generate_grid_lines


class MapCell:
    def __init__(self, cell_index, pointcloud_gt, pointcloud_cnd, options, fill_metrics = True):
        self.cell_index = cell_index
        self.metrics = {}
        self.options = options
        if fill_metrics:        
            if not pointcloud_gt.is_empty() and not pointcloud_cnd.is_empty():
                self.metrics["quality"], self.metrics["completeness"], self.metrics["artifacts"], self.metrics["resolution"], self.metrics["accuracy"]= calculate_complete_quality_metric(pointcloud_gt, pointcloud_cnd, options["e"], options["wc"], options["wt"], options["wr"], options["wa"])
            else:
                self.metrics["completeness"] = 0
                self.metrics["artifacts"] = 0
                self.metrics["resolution"] = 0
                self.metrics["accuracy"] = 0
                self.metrics["quality"] = 1.0
                
                                                                         

def parse_mapmetric_cells(cell_index, options, cell_metrics):
    cell = MapCell(cell_index, None, None, options, fill_metrics = False)
    cell.metrics = cell_metrics
    return cell

def get_list_from_string(cell_index):
    cell_indx_val_tmp = cell_index.replace("[", "").replace("]", "").split(" ")
    cell_indx_val = np.array([int(x) for x in cell_indx_val_tmp if x.strip() != ""])
    return cell_indx_val


def parse_mapmetric_config(config_file):
    with open(config_file) as f:
        config = json.load(f)
        map_metric = MapMetricManager(config["gt_file"], config["cnd_file"], config["cell_size"], config["options"])
        for cell_index in config["metrics"]:
            # cell_indx_val_tmp = cell_index.replace("[", "").replace("]", "").split(" ")
            # cell_indx_val = np.array([int(x) for x in cell_indx_val_tmp if x.strip() != ""])
            map_metric.metriccells[cell_index] = parse_mapmetric_cells(get_list_from_string(cell_index), config["options"], config["metrics"][cell_index])
        return map_metric
    


GT_COLOR = np.array([0, 1, 0])
CND_COLOR = np.array([0, 0, 1])
GREEN_COLOR = np.array([0, 1, 0])
RED_COLOR = np.array([1, 0, 0])


class MapMetricManager:
    def __init__(self, gt_file, cnd_file, chunk_size, metric_options = {"e": 0.1, "MPD": 100}):

        self.gt_file = gt_file
        self.cnd_file = cnd_file

        self.pointcloud_GT = o3d.io.read_point_cloud(gt_file)
        self.pointcloud_Cnd = o3d.io.read_point_cloud(cnd_file)

        self.pointcloud_GT.paint_uniform_color(GT_COLOR)
        self.pointcloud_Cnd.paint_uniform_color(CND_COLOR)

        self.chunk_size = chunk_size
        metric_options["r"] = chunk_size
        #compute the min bound of the pointcloud
        bb1 = self.pointcloud_Cnd.get_axis_aligned_bounding_box()
        bb2 = self.pointcloud_GT.get_axis_aligned_bounding_box()

        self.min_bound = np.minimum(bb1.min_bound, bb2.min_bound)
        self.max_bound = np.maximum(bb1.max_bound, bb2.max_bound)

        #print(self.min_bound, self.max_bound)

        self.cell_dim = (np.ceil((self.max_bound - self.min_bound) / self.chunk_size)).astype(int)
        self.max_bound = self.min_bound + self.cell_dim * self.chunk_size

        print("Dimension of each cell: ", self.cell_dim)

        self.metriccells = {}

        self.options = metric_options

    def reset(self, chunk_size, metric_options = {"e": 0.1, "MPD": 100}):
        self.metriccells = {}
        self.chunk_size = chunk_size
        self.cell_dim = (np.ceil((self.max_bound - self.min_bound) / self.chunk_size)).astype(int)
        self.max_bound = self.min_bound + self.cell_dim * self.chunk_size
        self.options = metric_options
        print("Dimension of each cell: ", self.cell_dim)        

    #visualize pointcloud
    def visualize(self):
        #visualize the pointcloud
        self.pointcloud_GT.paint_uniform_color([1, 0, 0])
        self.pointcloud_Cnd.paint_uniform_color([0, 1, 0])

        o3d.visualization.draw_geometries([self.pointcloud_GT, self.pointcloud_Cnd])

    def get_heatmap(self, metric_name):
        heatmap = copy.deepcopy(self.pointcloud_GT) #o3d.geometry.PointCloud()
        heatmap.paint_uniform_color([0, 0, 0])
        colors = np.zeros((len(heatmap.points), 3))
        for cell_index in self.metriccells:
            cell = self.metriccells[cell_index]
            cell_index_vals = get_list_from_string(cell_index)
            cell_index_next = cell_index_vals + np.array([1, 1, 1])

            min_bound, max_bound = get_cropping_bound(self.min_bound, self.chunk_size, cell_index_vals, cell_index_next)
            #print(min_bound, max_bound)
            bbox = o3d.geometry.AxisAlignedBoundingBox(min_bound=min_bound, max_bound=max_bound)

            col_indx = bbox.get_point_indices_within_bounding_box(heatmap.points)
            
            color = cell.metrics[metric_name] * GREEN_COLOR + (1-cell.metrics[metric_name]) * RED_COLOR
            #colors[col_indx] = [1-cell.metrics[metric_name], cell.metrics[metric_name], 0]
            colors[col_indx] = color
            #cropped_gt.paint_uniform_color([cell.metrics[metric_name], 0, 0])

            #cell_center = self.min_bound + (cell.cell_index + 0.5) * self.chunk_size
            #heatmap.points.append(cell_center)
        heatmap.colors = o3d.utility.Vector3dVector(colors) # append([cell.metrics[metric_name], 0, 0])
        return heatmap
    
    #visualize pointcloud heatmap
    def visualize_heatmap(self, metric_name, save=False, filename="test_heatmap.pcd"):
        #visualize the pointcloud
        heatmap = self.get_heatmap(metric_name)
        #heatmap.paint_uniform_color([1, 0, 0])
        if save:
            o3d.io.write_point_cloud(filename, heatmap)
        o3d.visualization.draw_geometries([heatmap])

    #visualize pointcloud with grid
    def visualize_cropped_point_cloud(self, chunk_size, min_cell_index, max_cell_index, save=False, filename="test.pcd"):
        #visualize the pointcloud

        cropped_gt, _ = get_cropped_point_cloud(self.pointcloud_GT, self.min_bound, chunk_size, min_cell_index, max_cell_index)
        cropped_gt.paint_uniform_color([1, 0, 0])
        cropped_candidate, _ = get_cropped_point_cloud(self.pointcloud_Cnd, self.min_bound, chunk_size, min_cell_index, max_cell_index)
        #cropped_candidate = self.pointcloud_Cnd.crop(bbox)
        cropped_candidate.paint_uniform_color([0, 1, 0])
        
        if save:
            o3d.io.write_point_cloud(filename+"_gt.pcd", cropped_gt)
            o3d.io.write_point_cloud(filename+"_cnd.pcd", cropped_candidate)
        o3d.visualization.draw_geometries([cropped_gt, cropped_candidate])


    def iterate_cells(self):
        #iterate through all the Cells
        for i in range(int(self.cell_dim[0])):
            for j in range(int(self.cell_dim[1])):
                for k in range(int(self.cell_dim[2])):
                    min_cell_index = np.array([i, j, k])
                    max_cell_index = np.array([i+1, j+1, k+1])
                    #print(min_cell_index, max_cell_index)
                    yield min_cell_index, max_cell_index
  
    def print_points_per_cell(self):
        pcd_list = []
        for min_cell_index, max_cell_index in self.iterate_cells():
            
            cropped_gt, _ = get_cropped_point_cloud(self.pointcloud_GT, self.min_bound, self.chunk_size, min_cell_index, max_cell_index)
            cropped_candidate, _ = get_cropped_point_cloud(self.pointcloud_Cnd, self.min_bound, self.chunk_size, min_cell_index, max_cell_index)
            if cropped_gt.is_empty() or cropped_candidate.is_empty():
                #print("CELL: ", min_cell_index, max_cell_index, end="\t" )
                #print("EMPTY")
                pass
            else:
                #print()                
                pcd_list.append(cropped_gt)
                pcd_list.append(cropped_candidate)


        grid_lines = generate_grid_lines(self.min_bound, self.max_bound, self.cell_dim)

        for line in grid_lines:
            pcd_list.append(line)

        o3d.visualization.draw_geometries(pcd_list)

    def compute_metric_old(self, filename="test.json"):
        #iterate through all the Cells
        metric_results = {}
        for min_cell_index, max_cell_index in self.iterate_cells():
            
            cropped_gt, _ = get_cropped_point_cloud(self.pointcloud_GT, self.min_bound, self.chunk_size, min_cell_index, max_cell_index)
            cropped_candidate, _ = get_cropped_point_cloud(self.pointcloud_Cnd, self.min_bound, self.chunk_size, min_cell_index, max_cell_index)
            if cropped_gt.is_empty() and cropped_candidate.is_empty():
                pass
            else:

                self.metriccells[str(min_cell_index)] =  MapCell(min_cell_index,cropped_gt, cropped_candidate, self.options)
                
                print(self.metriccells[str(min_cell_index)].metrics)
                metric_results[str(min_cell_index)] = self.metriccells[str(min_cell_index)].metrics
                                                                 
        with open(filename, 'w') as fp:
            json.dump(metric_results, fp, indent=4)


    def compute_metric(self, filename ="test.json"):

        from multiprocess import Process, Manager
        def f(d, min_cell_index,cropped_gt, cropped_candidate):
            d[str(min_cell_index)] = MapCell(min_cell_index,cropped_gt, cropped_candidate, self.options)
            print(d[str(min_cell_index)].metrics)

     
        manager = Manager()
        d = manager.dict()

        metric_results = {}
        job = []
        # Add tqdm to show progress
        for min_cell_index, max_cell_index in self.iterate_cells():
        # for min_cell_index, max_cell_index in self.iterate_cells():
            
            cropped_gt, _ = get_cropped_point_cloud(self.pointcloud_GT, self.min_bound, self.chunk_size, min_cell_index, max_cell_index)
            cropped_candidate, _ = get_cropped_point_cloud(self.pointcloud_Cnd, self.min_bound, self.chunk_size, min_cell_index, max_cell_index)
            if cropped_gt.is_empty() and cropped_candidate.is_empty():
                pass
            else:
                job.append(Process(target=f, args=(d, min_cell_index,cropped_gt, cropped_candidate)))
                #self.metriccells[str(min_cell_index)] =  MapCell(min_cell_index,cropped_gt, cropped_candidate, self.options)
                
                #print(self.metriccells[str(min_cell_index)].metrics)
                #metric_results[str(min_cell_index)] = self.metriccells[str(min_cell_index)].metrics
        _ = [p.start() for p in job]
        _ = [p.join() for p in job]

        self.metriccells= copy.deepcopy(d)
        metric_results["metrics"]={}
        for key in self.metriccells.keys():
           metric_results["metrics"][key] = self.metriccells[key].metrics

        metric_results["cell_size"] = self.chunk_size
        metric_results["cell_dim"] = self.cell_dim.flatten().tolist()
        metric_results["min_bound"] = self.min_bound.flatten().tolist()
        metric_results["max_bound"] = self.max_bound.flatten().tolist()
        metric_results["options"] = self.options
        metric_results["gt_file"] = self.gt_file
        metric_results["cnd_file"] = self.cnd_file


        quality_list = [metric_results["metrics"][key]["quality"] for key in metric_results["metrics"].keys()]
        average_quality = np.mean(quality_list)
        print("Average Quality: ", average_quality)
        quality_var = np.var(quality_list)
        print("Variance for Quality: ", quality_var)

        # Calculate average resolution
        resolution_list = [metric_results["metrics"][key]['resolution'] for key in metric_results["metrics"].keys()]
        average_resolution = np.mean(resolution_list)
        print("Average Resolution: ", average_resolution)
        resolution_var = np.var(resolution_list)
        print("Variance for Resolution: ", resolution_var)

        # Calculate average incompleteness
        incompleteness_list = [metric_results["metrics"][key]['incompleteness'] for key in metric_results["metrics"].keys()]
        average_incompleteness = np.mean(incompleteness_list)
        print("Average Incompleteness: ", average_incompleteness)
        incompleteness_var = np.var(incompleteness_list)
        print("Variance for Incompleteness: ", incompleteness_var)

        # Calculate average accuracy
        accuracy_list = [metric_results["metrics"][key]['accuracy'] for key in metric_results["metrics"].keys()]
        average_accuracy = np.mean(accuracy_list)
        print("Average Accuracy: ", average_accuracy)
        accuracy_var = np.var(accuracy_list)
        print("Variance for Accuracy: ", accuracy_var)


        # Calculate average artifacts
        artifacts_list = [metric_results["metrics"][key]['artifacts'] for key in metric_results["metrics"].keys()]
        average_artifacts = np.mean(artifacts_list)
        print("Average Artifacts: ", average_artifacts)
        artifacts_var = np.var(artifacts_list)
        print("Variance for Artifacts: ", artifacts_var)

        with open(filename, 'w+') as fp:
            metric_results["Total"] = {
                "Average Incompleteness": average_incompleteness,
                "Incompleteness Variance": incompleteness_var,
                "Average Artifacts": average_artifacts,
                "Artifacts Variance": artifacts_var,
                "Average Accuracy": average_accuracy,
                "Accuracy Variance": accuracy_var,
                "Average Resolution": average_resolution,
                "Resolution Variance": resolution_var,
                "Average Quality": average_quality,
                "Quality Variance": quality_var
            }
            json.dump(metric_results, fp, indent=4)
            

   