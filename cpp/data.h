#ifndef DATA_H
#define DATA_H

#include <stdint.h>

#include "config.h"

typedef struct __attribute__((packed)) {
	wind_t data[NUM_LEVELS][NUM_VARIABLES];
} wind_data;

typedef struct {
	int64_t time;
	wind_data *data;
	int fd;
} data_file;

typedef struct {
	int lat;
	int lon;
} point;

template<class Float>
struct wind_vector {
	Float u;
	Float v;
};

void load_data(const char *dname);
wind_data *get_data_at_point(data_file*, point);
point get_base_neighbor(float, float);
point get_nearest_neighbor(float, float);

extern data_file *files;
extern int num_files;

#endif
