# Prometheus Custom Service Discovery
In Trigo's solution there are many proprietary sensors based on embedded microcontrollers running bare-metal OS under hard resources limit (low cpu, low memory). Those sensors cannot run any modern tools such as Docker, Consul agents and so on but do expose an http server with a dedicated metrics endpoint.

In addition, the store operators can change the participating sensors so the inventory of sensors can be updated quite often.

In this exercise, we will implement a custom service discovery mechanism for [Prometheus](https://prometheus.io/). This will ensure that Prometheus continues to monitor the correct sensor inventory, even as the sensor configuration changes dynamically.

# Exercise
The [inventory service](./inventory_server/) will be used to expose an http endpoint that yields a list of hosts of the current active sensors.

Specifically, invoking the following command:
```
curl -XGET http://localhost:1337/inventory
```
will yield the current sensors hostnames to monitor:
```
[
    "sensor_1",
    "sensor_2",
    "sensor_12",
    ...
]
```

Your goal in this exercise is to:
* Implement a custom service discovery for Prometheus which queries the described endpoint (in the `inventory service`) and yields a target group containing the sensors targets.
* Write a minimal docker-compose / helm chart that runs the entire stack, having a Prometheus instance trying to scrape the sensors inventory with an exposed HTTP port (tcp/9090).

# Additional Notes
* Don't modify the `inventory service` code.
* Fork this repository, upload your solution, and then provide us with a link (and permissions).
* You have up to 2 hours to complete the exercise.
* Feel free to code it in any language you would like and use any framework / library / snippet of code you find.
* We are available to answer any questions you may have, so feel free to ask :smile:.
