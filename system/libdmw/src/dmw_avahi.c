#include "dmw_avahi.h"

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <avahi-common/domain.h>
#include <avahi-common/error.h>
#include <avahi-common/malloc.h>
#include <avahi-common/address.h>
#include <avahi-common/simple-watch.h>
#include <avahi-client/lookup.h>

static void client_callback(AvahiClient *client, AvahiClientState state, void *userdata);
static void browse_reply (
        AvahiServiceBrowser *b,
        AvahiIfIndex interface,
        AvahiProtocol protocol,
        AvahiBrowserEvent event,
        const char *name,
        const char *type,
        const char *domain,
        AvahiLookupResultFlags flags,
        void *userdata);
static void resolve_reply(
        AvahiServiceResolver *r,
        AvahiIfIndex interface,
        AvahiProtocol protocol,
        AvahiResolverEvent event,
        const char *name,
        const char *type,
        const char *domain,
        const char *host_name,
        const AvahiAddress *a,
        uint16_t port,
        AvahiStringList *txt,
        AvahiLookupResultFlags flags,
        void *userdata);

struct service_t {
    char *service;
    AvahiAddress address;
    uint16_t port;
    char *domain;
    int resolved;

    AvahiProtocol protocol;
    AvahiIfIndex interface;
    struct avahi_data_t *d;
};

struct avahi_data_t {
    AvahiClient *client;
    AvahiServiceBrowser *browser;
    AvahiSimplePoll *simple_poll;
    AvahiServiceResolver *resolver;

    struct service_t pub;
    struct service_t sub;

    struct service_t *cursvc;
};

static struct avahi_data_t data;

int avahi_init( const char *name )
{
    int error;

    if (! (data.simple_poll = avahi_simple_poll_new())) {
        goto fail;
    }

    if (! (data.client = avahi_client_new(
                  avahi_simple_poll_get(data.simple_poll),
                  0,
                  client_callback,
                  &data,
                  &error))) {
        goto fail;
    }

    if (! (data.browser = avahi_service_browser_new(
                  data.client,
                  AVAHI_IF_UNSPEC,
                  AVAHI_PROTO_UNSPEC,
                  name,    
                  NULL,
                  0,
                  browse_reply,
                  &data))) {
        goto fail;
    }

    if (strcmp( name, "_dmwpub._tcp" ) == 0 ) {
        data.cursvc = &data.pub;
        data.cursvc->resolved = 0;
    } else if (strcmp( name, "_dmwsub._tcp" ) == 0 ) {
        data.cursvc = &data.sub;
        data.cursvc->resolved = 0;
    } else {
        goto fail;
    } 

    return 0;

fail:
    if (data.client)
        avahi_client_free(data.client);

    if (data.simple_poll)
        avahi_simple_poll_free(data.simple_poll);

    return -1;
}

int avahi_loop( int msecs )
{
    while ( ! data.cursvc->resolved ) {
        if (avahi_simple_poll_iterate(data.simple_poll, msecs) != 0) {
            printf( "Failed simple loop\n" );
            if (data.client)
                avahi_client_free(data.client);

            if (data.simple_poll)
                avahi_simple_poll_free(data.simple_poll);
            return -1;
        }
    }
    return 0;

//    avahi_simple_poll_loop( data.simple_poll );
}

int avahi_get_pub_service( char *ip, int *port )
{
    avahi_address_snprint( ip, 16, &data.pub.address );
    *port = data.pub.port;
    return 0;
}

int avahi_get_sub_service( char *ip, int *port )
{
    avahi_address_snprint( ip, 16, &data.sub.address );
    *port = data.sub.port;
    return 0;
}

static void client_callback(AvahiClient *client, AvahiClientState state, void *userdata) {
    struct avahi_data_t *d = userdata;
    assert(d);

    switch (state) {

        case AVAHI_CLIENT_FAILURE:
            printf( "Client failure\n." );
            avahi_simple_poll_quit(d->simple_poll);
            break;

        case AVAHI_CLIENT_S_COLLISION:
        case AVAHI_CLIENT_S_REGISTERING:
        case AVAHI_CLIENT_S_RUNNING:
        case AVAHI_CLIENT_CONNECTING:
            ;
    }
}

static void browse_reply (
        AvahiServiceBrowser *b,
        AvahiIfIndex interface,
        AvahiProtocol protocol,
        AvahiBrowserEvent event,
        const char *name,
        const char *type,
        const char *domain,
        AvahiLookupResultFlags flags,
        void *userdata) {

    struct avahi_data_t *d = userdata;
    assert(d);

    switch (event) {
        case AVAHI_BROWSER_NEW: {
            printf("new service: %s\n", name);
            if ( protocol != AVAHI_PROTO_INET ) {
                break;
            }
            if (!(d->resolver = avahi_service_resolver_new(d->client,
                                                           interface,
                                                           protocol,
                                                           name,
                                                           type,
                                                           domain,
                                                           AVAHI_PROTO_UNSPEC,
                                                           0,
                                                           resolve_reply,
                                                           d->cursvc))) {
                printf("Failed to create service resolver for '%s': %s\n", name,
                               avahi_strerror(avahi_client_errno(d->client)));
            } else {
                /* Fill in missing data */
                d->cursvc->service = strdup(name);
                assert(d->cursvc->service);
                d->cursvc->domain = strdup(domain);
                assert(d->cursvc->domain);
                d->cursvc->interface = interface;
                d->cursvc->protocol = protocol;
                d->cursvc->d = d;
            }

            break;
        }

        case AVAHI_BROWSER_REMOVE:
            break;

        case AVAHI_BROWSER_FAILURE:
            printf("Service Browser failure '%s': %s\n", name,
                        avahi_strerror(avahi_client_errno(d->client)));

            avahi_simple_poll_quit(d->simple_poll);
            break;

        case AVAHI_BROWSER_CACHE_EXHAUSTED:
        case AVAHI_BROWSER_ALL_FOR_NOW:
            ;

    }
}

/* Called when a resolve call completes */
static void resolve_reply(
        AvahiServiceResolver *r,
        AvahiIfIndex interface,
        AvahiProtocol protocol,
        AvahiResolverEvent event,
        const char *name,
        const char *type,
        const char *domain,
        const char *host_name,
        const AvahiAddress *a,
        uint16_t port,
        AvahiStringList *txt,
        AvahiLookupResultFlags flags,
        void *userdata) {

    struct service_t *s = userdata;

    switch (event) {

        case AVAHI_RESOLVER_FOUND: {
            AvahiStringList *i;

            /* Look for the number of CPUs in TXT RRs */
            for (i = txt; i; i = i->next) {
                char *key, *value;

                if (avahi_string_list_get_pair(i, &key, &value, NULL) < 0)
                    continue;

                avahi_free(key);
                avahi_free(value);
            }

            if ( a->proto == AVAHI_PROTO_INET ) {
                s->address = *a;
                s->port = port;
                s->resolved = 1;
            }

            avahi_service_resolver_free(s->d->resolver);
            s->d->resolver = NULL;

            break;
        }

        case AVAHI_RESOLVER_FAILURE:

            printf("Failed to resolve service '%s': %s\n", name,
                           avahi_strerror(avahi_client_errno(s->d->client)));
            break;
    }

}


