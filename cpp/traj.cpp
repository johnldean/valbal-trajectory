#include <stdio.h>
#include <assert.h>

#include <adept.h>
using adept::adouble;

#include "data.h"
#include "sim.h"
#include "utils.h"
#include <random>
#define STORE_ALTITUDE

using namespace std;

void demo() {
	load_data(get_data_path("/proc/gfs_anl_0deg5"), 1500000000,1600000000);
	int t0 = 1541052000;
	float lat0 = 37.4241;
	float lon0 =  -122.1661 + 360;

	/* Fly at constant 14 km. This is the most simple controller. Other controllers
     * include simulating the Lasagna controller, or having a differentiable controller
     * that can be optimized. */
	float pressures[120];
	for (int i=0; i<120; i++) pressures[i] = alt2p(14000);
	WaypointController<float> controller(t0, 3600, pressures);

    TIMEIT("Running simple sims",
        const int N = 200;
		/* This is just to run it faster, on multiplee threads. The scheduler isn't
         * strictly necessary. */
        Scheduler<float> sched(-1, N);
        for (int i=0; i<N; i++) {
            sched.add([&controller, i, t0, lat0, lon0]() {
                Simulation<float> sim(controller, i);
                sim.wind_default.sigma = 1;
                return sim.run(t0, lat0, lon0).lon;
            });
        }
        sched.finish();
    )
    for (int i=0; i<N; i++) {
        assert(sched.results[i] != 0);
    }

}

void stochasticGradients(){
	load_data(get_data_path("/proc/gfs_anl_0deg5"), 1500000000,1600000000);
	int t0 = 1541045606;
	int dt = 3600*6;
	const int N_RUNS = 50;
	float LR_H = 200000;
	const float alpha = 0.995;
	adept::Stack stack;
	TemporalParameters<adouble> params(t0, dt, 120*dt, 16000, 1000);
	for (int it=0; it<3000; it++){
		LR_H = LR_H*alpha;
		clock_t timer0 = clock();
		adouble obj_sum = 0;
		stack.new_recording();
		adouble objectives[N_RUNS];
		printf("active stack %p\n", adept::active_stack());

		for (int run=0; run<N_RUNS; run++) {
		printf("active stack %p\n", adept::active_stack());
			StochasticControllerApprox<adouble> controller(params, run*1019);
			LinInterpWind<adouble> wind;
			FinalLongitude<adouble> obj;
			EulerIntBal<adouble> in;
			Simulation<adouble> sim(controller, wind, obj, in, run + N_RUNS*(it==0));
			sim.tmax=60*60*100;
			sim.run(t0, 47.4289, -19.6931+360);
			objectives[run] = obj.getObjective();
		}

		for (int run=0; run<N_RUNS; run++) obj_sum += objectives[run];
		obj_sum = obj_sum/((float)N_RUNS);
		obj_sum.set_gradient(1.0);
		stack.compute_adjoint();
		double grad_mag = params.apply_gradients(LR_H);

		float dt = (clock() - timer0)/((double)CLOCKS_PER_SEC)*1000;
		printf("Took %.2f ms, obj: %f, gradient norm %e\n",dt,VAL(obj_sum), grad_mag);
	}
}

int main() {
	printf("ValBal trajectory optimization.\n");
	printf("This program is highly cunning and, on the face of it, not entirely wrong.\n");

	demo();
	exit(1);

	//load_data(get_data_path("/proc/gfs_pred_0deg5/20181021_12"), 1500000000,1600000000);
	//load_data("../ignored/proc/euro_anl", 1500000000,1600000000);
	//load_data("../ignored/proc/euro_fc", 1500000000,1600000000);
	//load_data("../proc", 1500000000,1600000000);

	/*wind_data *sample = get_data_at_point(files+0, {42, 120});
	printf("(u,v) %hd %hd\n", sample->data[4][0], sample->data[4][1]);

	point base = get_base_neighbor(69.5, 60.6);
	point near = get_nearest_neighbor(69.5, 60.9);
	printf("(%d,%d) (%d, %d)\n", base.lat, base.lon, near.lat, near.lon);
	*/
	//simpleSim67();
	//ssi71Sims();
	//gradientsStuff();
	//MLestimation();
	stochasticGradients();
	//saveSpaceshot();
	//stocasticGradients();
}
