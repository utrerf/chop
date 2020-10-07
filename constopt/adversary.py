import torch
from torch.autograd import Variable
import numpy as np


class Adversary:
    def __init__(self, shape, constraint, optimizer_class):
        self.delta = Variable(torch.zeros(shape), requires_grad=True)
        self.optimizer = optimizer_class([self.delta], constraint)
        self.constraint = constraint

    def perturb(self, data, target, model, criterion,
                step_size, tol=1e-3, iterations=None,
                store=None):
        model.eval()
        ii = 0
        if "FW" in self.optimizer.name:
            print("FW")
            step_size = 0.

        gap = torch.tensor(np.inf)
        while gap.item() > tol:
            if ii == iterations:
                break

            self.optimizer.zero_grad()
            output = model(data + self.delta)
            loss = -criterion(output, target)
            print(loss.item())
            loss.backward()

            with torch.no_grad():
                gap = self.constraint.fw_gap(self.delta.grad, self.delta)

            self.optimizer.step(step_size)
            ii += 1

            # Logging
            if store:
                # Might be better to use the same name for all optimizers, to get
                # only one plot
                def norm(x):
                    if self.constraint.p == 1:
                        return abs(x).sum()
                    if self.constraint.p == 2:
                        return (x ** 2).sum()
                    if self.constraint.p == np.inf:
                        return abs(x).max()
                    raise NotImplementedError("We've only implemented p = 1, 2, np.inf")
                p = self.constraint.p
                table_name = "L" + str(int(p)) + " ball" if p != np.inf else "Linf Ball"
                store.log_table_and_tb(table_name,
                                       {'func_val': -loss.item(),
                                        'FW gap': gap.item(),
                                        'norm delta': norm(self.delta)
                                        })
                store[table_name].flush_row()

        return loss, self.delta
