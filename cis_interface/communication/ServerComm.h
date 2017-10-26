#include <CommBase.h>
#include <DefaultComm.h>
#include <comm_header.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISSERVERCOMM_H_
#define CISSERVERCOMM_H_

// Handle is recv address
// Info is response

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_server_address(comm_t *comm) {
  comm->type = _default_comm;
  return new_default_address(comm);
};

/*!
  @brief Initialize a server communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_server_comm(comm_t *comm) {
  int ret;
  // Called to create temp comm for send/recv
  if ((strlen(comm->name) == 0) && (strlen(comm->address) > 0)) {
    comm->type = _default_comm;
    return init_default_comm(comm);
  }
  // Called to initialize/create server comm
  char *seri_in = (char*)malloc(strlen(comm->direction) + 1);
  strcpy(seri_in, comm->direction);
  comm_t *handle = (comm_t*)malloc(sizeof(comm_t));
  if (strlen(comm->name) == 0) {
    handle[0] = new_comm_base(comm->address, "recv", _default_comm, (void*)seri_in);
    sprintf(handle->name, "server_request.%s", comm->address);
  } else {
    handle[0] = init_comm_base(comm->name, "recv", _default_comm, (void*)seri_in);
  }
  ret = init_default_comm(handle);
  /* printf("init_server_comm: name = %s, type=%d, address = %s\n", */
  /* 	 handle->name, handle->type, handle->address); */
  strcpy(comm->direction, "recv");
  comm->handle = (void*)handle;
  comm->always_send_header = 1;
  comm_t **info = (comm_t**)malloc(sizeof(comm_t*));
  info[0] = NULL;
  comm->info = (void*)info;
  free(seri_in);
  return ret;
};

/*!
  @brief Perform deallocation for server communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_server_comm(comm_t *x) {
  if (x->handle != NULL) {
    comm_t *handle = (comm_t*)(x->handle);
    free_default_comm(handle);
    free(x->handle);
    x->handle = NULL;
  }
  if (x->info != NULL) {
    comm_t **info = (comm_t**)(x->info);
    if (*info != NULL) {
      free_default_comm(*info);
      free(*info);
    }
    free(info);
    x->info = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int server_comm_nmsg(const comm_t x) {
  comm_t *handle = (comm_t*)(x.handle);
  int ret = default_comm_nmsg(*handle);
  return ret;
};

/*!
  @brief Send a message to the comm.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int server_comm_send(const comm_t x, const char *data, const int len) {
  cislog_debug("server_comm_send(%s): %d bytes", x.name, len);
  if (x.info == NULL) {
    cislog_error("server_comm_send(%s): no response comm registered", x.name);
    return -1;
  }
  comm_t **res_comm = (comm_t**)(x.info);
  if (res_comm[0] == NULL) {
    cislog_error("server_comm_send(%s): no response comm registered", x.name);
    return -1;
  }
  return default_comm_send((*res_comm)[0], data, len);
};

/*!
  @brief Receive a message from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int server_comm_recv(comm_t x, char *data, const int len) {
  cislog_debug("server_comm_recv(%s)", x.name);
  if (x.handle == NULL) {
    cislog_error("server_comm_recv(%s): no request comm registered", x.name);
    return -1;
  }
  comm_t *req_comm = (comm_t*)(x.handle);
  int ret = default_comm_recv(*req_comm, data, len);
  if (ret < 0)
    return ret;
  // Return EOF
  if (is_eof(data)) {
    return ret;
  }
  // Initialize new comm from received address
  comm_head_t head = parse_comm_header(data, ret);
  if (!(head.valid)) {
    cislog_error("server_comm_recv(%s): Error parsing header.", x.name);
    return -1;
  }
  // If there is not a response address
  if (strlen(head.response_address) == 0) {
    cislog_error("server_comm_recv(%s): No response address in message.", x.name);
    return -1;
  }
  strcpy(x.address, head.id);
  comm_t **res_comm = (comm_t**)(x.info);
  res_comm[0] = (comm_t*)realloc(res_comm[0], sizeof(comm_t));
  res_comm[0][0] = new_comm_base(head.response_address, "send", _default_comm,
				 x.serializer.info);
  sprintf(res_comm[0]->name, "server_response.%s", res_comm[0]->address);
  int newret;
  newret = init_default_comm(res_comm[0]);
  if (newret < 0) {
    cislog_error("server_comm_recv(%s): Could not initialize response comm.", x.name);
    return newret;
  }
  return ret;
};

#endif /*CISSERVERCOMM_H_*/
