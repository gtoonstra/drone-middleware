import select
import sys
import pybonjour

timeout  = 5

class ServiceResolver( object ):
    def resolve_record( self, recname ):
        self.recname = recname
        self.hostip = None
        self.port = None
        self.resolved = []
        self.browse_sdRef = pybonjour.DNSServiceBrowse(regtype = self.recname,
                                          callBack = self.browse_callback)
        try:
            try:
                while not self.resolved:
                    ready = select.select([self.browse_sdRef], [], [])
                    if self.browse_sdRef in ready[0]:
                        pybonjour.DNSServiceProcessResult(self.browse_sdRef)
            except KeyboardInterrupt:
                pass
        finally:
            self.browse_sdRef.close()

        return self.hostip, self.port

    def resolve_callback(self, sdRef, flags, interfaceIndex, errorCode, fullname,
                     hosttarget, port, txtRecord):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            self.hostip = hosttarget
            self.port = port
            self.resolved.append(True)

    def browse_callback(self, sdRef, flags, interfaceIndex, errorCode, serviceName,
                    regtype, replyDomain):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return

        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            return

        resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                    interfaceIndex,
                                                    serviceName,
                                                    regtype,
                                                    replyDomain,
                                                    self.resolve_callback)

        try:
            while not self.resolved:
                ready = select.select([resolve_sdRef], [], [], timeout)
                if resolve_sdRef not in ready[0]:
                    print 'Resolve timed out'
                    break
                pybonjour.DNSServiceProcessResult(resolve_sdRef)
        finally:
            resolve_sdRef.close()


