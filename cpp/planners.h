#ifndef PLANNERS_H
#define PLANNERS_H


#include "sim.h"
#include "objectives.h"



class StochasticMPC {
public: 
	typedef struct{
		sim_state<float> state0;
		int tmax = 120*60*60;				// max sim time in seconds
		int cmd_dt = 3600*6;				// time between comand waypoints
		int init_cmd_dt = 60*60*24;
		int n_samples = 50;					// Number of samples per batch
		int n_iters_max = 1000;				// Number of itterations max
		int n_iters_min = 10;				// Number of itterations min
		int n_starts = 50;					// Numer of random starts to try
		int opt_sign = 1;					// sign on the optimization
		int fname_offset = 0;				// offset on the file name numbers
		bool write_files = true;
		void fromJson(std::string conf){
    		Json::Reader reader;
    		Json::Value obj;
    		reader.parse(conf, obj);
    		PARSE_I(tmax);
			PARSE_I(cmd_dt);
			PARSE_I(init_cmd_dt);
			PARSE_I(n_samples);
			PARSE_I(n_iters_max);
			PARSE_I(n_iters_min);
			PARSE_I(n_starts);
			PARSE_I(opt_sign);
			PARSE_I(fname_offset);
			PARSE_B(write_files);
    	};
	} Config;

	typedef struct {
		double lr_set  = 200000;
		double lr_tol  = 100000;
		double alpha   = 0.99999;
		double tol_min = 200;
		double tol_max = 3000;
		double set_min = 12800;
		double set_max = 19000;
		double bound_min = 12500;
		double bound_max = 19000;
		double obj_filter_corner = 0.03;
		double convergence_thresh = 0.1;
		void fromJson(std::string conf){
    		Json::Reader reader;
    		Json::Value obj;
    		reader.parse(conf, obj);
			PARSE_D(lr_set);
			PARSE_D(lr_tol);
			PARSE_D(alpha);
			PARSE_D(tol_min);
			PARSE_D(tol_max);
			PARSE_D(set_min);
			PARSE_D(set_max);
			PARSE_D(bound_min);
			PARSE_D(bound_max);
			PARSE_D(obj_filter_corner);
			PARSE_D(convergence_thresh);
    	};
	} HyperParams;
	HyperParams hparams;
	FILE *file;
	bool save_to_file = 1;



	StochasticMPC(const char* input_db, sim_state<float> state0, const std::string& objconf_);
	TemporalParameters<float> run();
	DataHandler data;
	Config conf;
	std::string objconf;
	//FinalLongitude<adouble> objfn;
};

class SpatialPlanner {
public: 
	typedef struct{
		sim_state<float> state0;
		int tmax = 120*60*60;				// max sim time in seconds
		int cmd_dt = 3600*6;				// time between comand waypoints
		int n_samples = 50;					// Number of samples per batch
		int n_iters = 300;					// Number of itterations
		int n_starts;						// Numer of random starts to try
		int opt_sign = -1;					// sign on the optimization
		int fname_offset = 0;				// offset on the file name numbers
		bool write_files = true;
	} Config;
	SpatialPlanner(const char* input_db, sim_state<float> state0);
	adept::Stack stack;
	SpatiotemporalParameters<float> run();
	DataHandler data;
	GradStep step;
	Config conf;
	//FinalLongitude<adouble> objfn;
};



#endif
